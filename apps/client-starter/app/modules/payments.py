"""
Payments Module -- Pluggable Payment Provider Framework
=======================================================
Config-driven payment PROVIDER INTERFACE so a client can plug in
any processor without modifying checkout logic.

DEFAULT: Stripe (industry standard, recommended).
Alternatives available for operators who need them: ACH, BarterPay,
ClickBrick, crypto, or manual/offline payment.

HARD RULE: NO real payment credentials anywhere. This module
provides the FRAMEWORK + stubs only. The operator fills in their
own API keys via environment variables.

  ==========================================
  OPERATOR: CHOOSE PAYMENT PROCESSOR
  ==========================================
  Set config.py -> payment -> active_provider to one of:
    "stripe"      - Stripe Checkout (DEFAULT, recommended)
    "manual"      - No online payment (offline invoicing)
    "ach_direct"  - ACH bank transfer
    "barterpay"   - BarterPay integration
    "clickbrick"  - ClickBrick ACH
    "crypto"      - Cryptocurrency
  Then fill in the provider-specific config keys.
  ==========================================

Modules that need to collect payment (e.g. ecommerce checkout)
call:
    from modules.payments import get_payment_provider
    provider = get_payment_provider()
    result = provider.initiate_payment(order_id, amount_cents, metadata,
                                       success_url=ABSOLUTE, cancel_url=ABSOLUTE)

WEBHOOK SECURITY (yourAICIV hardening)
  - Every provider authenticates its webhook in verify_webhook(). Stripe uses
    stripe.Webhook.construct_event() over the RAW body (HMAC, 300s
    tolerance). Stub providers use a static X-Webhook-Secret header and MUST
    get a real signature check before they are used for real money.
  - Every event id is recorded in processed_events; repeats are ignored.
  - An order is marked paid ONLY when the event says payment_status ==
    "paid", its amount equals the order total in cents, its currency matches,
    and it references the checkout session we created for that order.
"""

import os
import sys
import json
import hmac as _hmac
import hashlib
from datetime import datetime
from abc import ABC, abstractmethod

from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, session, jsonify)

payments_bp = Blueprint('payments', __name__,
                        template_folder='../templates')


class WebhookAuthError(Exception):
    """Webhook could not be authenticated (bad/missing signature or secret)."""


def _absolute(url):
    """True for https URLs (http allowed only for loopback testing)."""
    return bool(url) and (url.startswith('https://')
                          or url.startswith('http://127.0.0.1')
                          or url.startswith('http://localhost'))


def _is_admin():
    """Admin check shared with app.py (honours session revocation)."""
    from flask import current_app
    return current_app.config['_helpers']['is_admin']()


# =========================================================================
#  PROVIDER INTERFACE (Abstract Base)
# =========================================================================

class PaymentProvider(ABC):
    """Abstract base for all payment providers.

    Every provider must implement these methods. The checkout flow
    calls them generically -- the provider handles the specifics.
    """

    def __init__(self, provider_config):
        self.config = provider_config
        self.label = provider_config.get('label', 'Payment')
        self.description = provider_config.get('description', '')

    @abstractmethod
    def initiate_payment(self, order_id, amount_cents, metadata=None,
                         success_url=None, cancel_url=None):
        """Start a payment flow.

        Args:
            order_id: Internal order identifier
            amount_cents: Amount in cents (integer)
            metadata: dict of extra data (customer name, email, etc.)

        Returns:
            dict with keys:
                status: "pending" | "redirect" | "completed" | "error"
                redirect_url: URL to send customer to (if status=redirect)
                payment_ref: provider's reference ID
                message: human-readable message
        """
        pass

    @abstractmethod
    def check_status(self, payment_ref):
        """Check the status of a previously initiated payment.

        Returns:
            dict with keys:
                status: "pending" | "completed" | "failed" | "refunded"
                payment_ref: provider's reference ID
                details: dict of provider-specific details
        """
        pass

    @abstractmethod
    def handle_webhook(self, request_data):
        """Process an incoming webhook/callback from the provider.

        Returns:
            dict with keys:
                order_id: the order this webhook relates to
                status: new status
                payment_ref: provider reference
        """
        pass

    def verify_webhook(self, req, raw_body, client_cfg):
        """Authenticate an incoming webhook and return the parsed event dict.

        Default (stub providers): static shared secret in X-Webhook-Secret,
        compared in constant time. This is NOT a payload signature and has no
        replay protection beyond event-id dedup; replace it with the real
        provider's signature scheme before taking money through it.
        """
        webhook_secret = client_cfg.get('payment_webhook_secret', '')
        if not webhook_secret:
            raise WebhookAuthError('PAYMENT_WEBHOOK_SECRET not configured')
        provided = req.headers.get('X-Webhook-Secret', '')
        if not provided or not _hmac.compare_digest(provided, webhook_secret):
            raise WebhookAuthError('invalid X-Webhook-Secret')
        try:
            return json.loads(raw_body or b'{}')
        except ValueError:
            raise WebhookAuthError('body is not JSON')

    def get_checkout_fields(self):
        """Return list of extra form fields needed at checkout.

        Returns:
            list of dicts: [{"name": "...", "label": "...", "type": "text", "required": True}]
        """
        return []

    def get_display_info(self):
        """Return info for displaying this provider in the checkout UI."""
        return {
            'label': self.label,
            'description': self.description,
        }


# =========================================================================
#  PROVIDER IMPLEMENTATIONS (Stubs)
# =========================================================================

class ManualPaymentProvider(PaymentProvider):
    """Manual / offline payment. Order is placed; payment happens separately.
    This is the default safe option -- no online processing needed.
    """

    def initiate_payment(self, order_id, amount_cents, metadata=None,
                         success_url=None, cancel_url=None):
        return {
            'status': 'pending',
            'redirect_url': None,
            'payment_ref': f'manual-{order_id}',
            'message': 'Order placed. Payment details will be sent separately.',
        }

    def check_status(self, payment_ref):
        return {
            'status': 'pending',
            'payment_ref': payment_ref,
            'details': {'note': 'Manual payment -- check offline records.'},
        }

    def handle_webhook(self, request_data):
        return {'order_id': None, 'status': 'pending', 'payment_ref': None}


class StripeProvider(PaymentProvider):
    """Stripe Checkout -- industry standard payment processing (DEFAULT).

    Uses Stripe Checkout Sessions (redirect flow) for PCI-compliant
    card payments. The customer is redirected to Stripe's hosted checkout
    page and returned to the site after payment.

    OPERATOR: Fill in these environment variables:
      - STRIPE_SECRET_KEY       (from Stripe Dashboard > API keys)
      - STRIPE_WEBHOOK_SECRET   (from Stripe Dashboard > Webhooks)
    And set config values:
      - config.payment.providers.stripe.success_url
      - config.payment.providers.stripe.cancel_url
    """

    def initiate_payment(self, order_id, amount_cents, metadata=None,
                         success_url=None, cancel_url=None):
        secret_key = os.environ.get(
            self.config.get('secret_key_env', 'STRIPE_SECRET_KEY'), '')
        if not secret_key:
            return {
                'status': 'error',
                'redirect_url': None,
                'payment_ref': None,
                'message': 'Stripe not configured. Set STRIPE_SECRET_KEY in .env.',
            }

        try:
            import stripe
            stripe.api_key = secret_key

            meta = metadata or {}
            if not (_absolute(success_url) and _absolute(cancel_url)):
                return {
                    'status': 'error',
                    'redirect_url': None,
                    'payment_ref': None,
                    'message': 'Stripe needs absolute success/cancel URLs '
                               '(set CLIENT_PUBLIC_BASE_URL or config domain).',
                }
            if not isinstance(amount_cents, int) or amount_cents <= 0:
                return {'status': 'error', 'redirect_url': None,
                        'payment_ref': None, 'message': 'invalid amount'}
            params = dict(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': self.config.get('currency', 'usd'),
                        'unit_amount': amount_cents,
                        'product_data': {
                            'name': meta.get('description', f'Order #{order_id}'),
                        },
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                client_reference_id=str(order_id),
                metadata={'order_id': str(order_id)},
            )
            if meta.get('customer_email'):
                params['customer_email'] = meta['customer_email']
            checkout_session = stripe.checkout.Session.create(**params)

            return {
                'status': 'redirect',
                'redirect_url': checkout_session.url,
                'payment_ref': checkout_session.id,
                'message': 'Redirecting to Stripe Checkout...',
            }

        except ImportError:
            return {
                'status': 'error',
                'redirect_url': None,
                'payment_ref': None,
                'message': 'Stripe Python package not installed. Run: pip install stripe',
            }
        except Exception as e:
            # Detail is for the server log only; checkout shows buyers a
            # generic message.
            return {
                'status': 'error',
                'redirect_url': None,
                'payment_ref': None,
                'message': f'Stripe error: {type(e).__name__}: {e}',
            }

    def check_status(self, payment_ref):
        secret_key = os.environ.get(
            self.config.get('secret_key_env', 'STRIPE_SECRET_KEY'), '')
        if not secret_key:
            return {
                'status': 'pending',
                'payment_ref': payment_ref,
                'details': {'note': 'Stripe not configured.'},
            }

        try:
            import stripe
            stripe.api_key = secret_key
            session = stripe.checkout.Session.retrieve(payment_ref)

            status_map = {
                'complete': 'completed',
                'expired': 'failed',
                'open': 'pending',
            }
            return {
                'status': status_map.get(session.status, 'pending'),
                'payment_ref': payment_ref,
                'details': {
                    'stripe_status': session.status,
                    'payment_status': session.payment_status,
                    'amount_total': session.amount_total,
                    'currency': session.currency,
                },
            }
        except Exception as e:
            return {
                'status': 'pending',
                'payment_ref': payment_ref,
                'details': {'note': f'Error checking status: {e}'},
            }

    def verify_webhook(self, req, raw_body, client_cfg):
        """Stripe-Signature verification over the RAW request body."""
        secret = os.environ.get(
            self.config.get('webhook_secret_env', 'STRIPE_WEBHOOK_SECRET'), '')
        if not secret:
            raise WebhookAuthError('STRIPE_WEBHOOK_SECRET not configured')
        sig_header = req.headers.get('Stripe-Signature', '')
        if not sig_header:
            raise WebhookAuthError('missing Stripe-Signature')
        try:
            import stripe
        except ImportError:
            raise WebhookAuthError('stripe package not installed')
        try:
            stripe.Webhook.construct_event(raw_body, sig_header, secret)
        except (ValueError, stripe.SignatureVerificationError) as e:
            raise WebhookAuthError(f'signature verification failed: {type(e).__name__}')
        # The signature covers exactly these bytes; parse them ourselves.
        return json.loads(raw_body)

    def handle_webhook(self, event):
        """Map a VERIFIED Stripe event to an order update request."""
        event_type = event.get('type', '')
        obj = (event.get('data') or {}).get('object') or {}
        order_id = (obj.get('metadata') or {}).get('order_id') \
            or obj.get('client_reference_id')
        base = {
            'order_id': order_id,
            'payment_ref': obj.get('id'),
            'payment_status': obj.get('payment_status'),
            'amount_total': obj.get('amount_total'),
            'currency': (obj.get('currency') or '').lower(),
            'expected_currency': self.config.get('currency', 'usd').lower(),
        }
        if event_type in ('checkout.session.completed',
                          'checkout.session.async_payment_succeeded'):
            return dict(base, status='completed')
        if event_type in ('checkout.session.expired',
                          'checkout.session.async_payment_failed'):
            return dict(base, status='failed')
        return {'order_id': None, 'status': 'pending', 'payment_ref': None}


class ACHDirectProvider(PaymentProvider):
    """ACH bank transfer -- alternative to card processing.

    STUB: Implement actual ACH API calls when provider is chosen.
    This could integrate with Dwolla, Plaid ACH, or direct bank API.

    OPERATOR: When ready, fill in:
      - config.payment.providers.ach_direct.api_key_env
      - config.payment.providers.ach_direct.vendor_id
    """

    def initiate_payment(self, order_id, amount_cents, metadata=None,
                         success_url=None, cancel_url=None):
        # STUB: In production, this would call the ACH provider's API
        # to initiate a bank transfer.
        api_key = os.environ.get(
            self.config.get('api_key_env', 'ACH_API_KEY'), '')
        if not api_key:
            return {
                'status': 'error',
                'redirect_url': None,
                'payment_ref': None,
                'message': 'ACH provider not configured. Contact admin.',
            }

        # Placeholder: would call ACH API here
        return {
            'status': 'pending',
            'redirect_url': None,
            'payment_ref': f'ach-stub-{order_id}',
            'message': 'ACH transfer initiated. Funds typically arrive in 2-3 business days.',
        }

    def check_status(self, payment_ref):
        return {
            'status': 'pending',
            'payment_ref': payment_ref,
            'details': {'note': 'ACH stub -- implement status check with real provider.'},
        }

    def handle_webhook(self, request_data):
        return {'order_id': None, 'status': 'pending', 'payment_ref': None}

    def get_checkout_fields(self):
        return [
            {'name': 'bank_routing', 'label': 'Routing Number', 'type': 'text', 'required': True},
            {'name': 'bank_account', 'label': 'Account Number', 'type': 'text', 'required': True},
            {'name': 'account_type', 'label': 'Account Type', 'type': 'select',
             'options': ['checking', 'savings'], 'required': True},
        ]


class BarterPayProvider(PaymentProvider):
    """BarterPay integration -- alternative payment provider.

    STUB: Implement actual BarterPay API calls when configured.

    OPERATOR: When ready, fill in:
      - config.payment.providers.barterpay.api_key_env
      - config.payment.providers.barterpay.merchant_url
    """

    def initiate_payment(self, order_id, amount_cents, metadata=None,
                         success_url=None, cancel_url=None):
        api_key = os.environ.get(
            self.config.get('api_key_env', 'BARTERPAY_API_KEY'), '')
        merchant_url = self.config.get('merchant_url', '')

        if not api_key or not merchant_url:
            return {
                'status': 'error',
                'redirect_url': None,
                'payment_ref': None,
                'message': 'BarterPay not configured. Contact admin.',
            }

        # Placeholder: would create BarterPay payment intent
        return {
            'status': 'redirect',
            'redirect_url': f'{merchant_url}/pay?ref=bp-stub-{order_id}',
            'payment_ref': f'bp-stub-{order_id}',
            'message': 'Redirecting to BarterPay...',
        }

    def check_status(self, payment_ref):
        return {
            'status': 'pending',
            'payment_ref': payment_ref,
            'details': {'note': 'BarterPay stub -- implement with real API.'},
        }

    def handle_webhook(self, request_data):
        return {'order_id': None, 'status': 'pending', 'payment_ref': None}


class ClickBrickProvider(PaymentProvider):
    """ClickBrick ACH -- alternative ACH processing.

    STUB: Implement actual ClickBrick API calls when configured.

    OPERATOR: When ready, fill in:
      - config.payment.providers.clickbrick.api_key_env
      - config.payment.providers.clickbrick.vendor_id
    """

    def initiate_payment(self, order_id, amount_cents, metadata=None,
                         success_url=None, cancel_url=None):
        api_key = os.environ.get(
            self.config.get('api_key_env', 'CLICKBRICK_API_KEY'), '')
        vendor_id = self.config.get('vendor_id', '')

        if not api_key or not vendor_id:
            return {
                'status': 'error',
                'redirect_url': None,
                'payment_ref': None,
                'message': 'ClickBrick not configured. Contact admin.',
            }

        # Placeholder: would call ClickBrick API here
        return {
            'status': 'pending',
            'redirect_url': None,
            'payment_ref': f'cb-stub-{order_id}',
            'message': 'ACH payment initiated via ClickBrick.',
        }

    def check_status(self, payment_ref):
        return {
            'status': 'pending',
            'payment_ref': payment_ref,
            'details': {'note': 'ClickBrick stub -- implement with real API.'},
        }

    def handle_webhook(self, request_data):
        return {'order_id': None, 'status': 'pending', 'payment_ref': None}

    def get_checkout_fields(self):
        return [
            {'name': 'bank_routing', 'label': 'Routing Number', 'type': 'text', 'required': True},
            {'name': 'bank_account', 'label': 'Account Number', 'type': 'text', 'required': True},
        ]


class CryptoPaymentProvider(PaymentProvider):
    """Cryptocurrency payment -- alternative provider.

    STUB: Implement actual crypto payment flow when configured.

    OPERATOR: When ready, fill in:
      - config.payment.providers.crypto.wallet_address
      - config.payment.providers.crypto.accepted_coins
    """

    def initiate_payment(self, order_id, amount_cents, metadata=None,
                         success_url=None, cancel_url=None):
        wallet = self.config.get('wallet_address', '')
        if not wallet:
            return {
                'status': 'error',
                'redirect_url': None,
                'payment_ref': None,
                'message': 'Crypto payment not configured. Contact admin.',
            }

        amount_usd = amount_cents / 100.0
        coins = ', '.join(self.config.get('accepted_coins', ['BTC']))
        return {
            'status': 'pending',
            'redirect_url': None,
            'payment_ref': f'crypto-{order_id}',
            'message': f'Send ${amount_usd:.2f} equivalent in {coins} to wallet. '
                       f'Order will be confirmed upon receipt.',
        }

    def check_status(self, payment_ref):
        return {
            'status': 'pending',
            'payment_ref': payment_ref,
            'details': {'note': 'Crypto stub -- implement blockchain verification.'},
        }

    def handle_webhook(self, request_data):
        return {'order_id': None, 'status': 'pending', 'payment_ref': None}


# =========================================================================
#  PROVIDER REGISTRY
# =========================================================================

PROVIDER_CLASSES = {
    'stripe': StripeProvider,
    'manual': ManualPaymentProvider,
    'ach_direct': ACHDirectProvider,
    'barterpay': BarterPayProvider,
    'clickbrick': ClickBrickProvider,
    'crypto': CryptoPaymentProvider,
}


def get_payment_provider(provider_name=None, with_name=False):
    """Get the configured payment provider instance.

    Args:
        provider_name: Override the active provider (optional).
                       Defaults to config.payment.active_provider.

    Returns:
        PaymentProvider instance

    Raises:
        ValueError if provider is unknown or not configured.
    """
    from flask import current_app
    payment_config = current_app.config['_helpers']['config'].get('payment', {})

    if provider_name is None:
        provider_name = payment_config.get('active_provider', 'manual')

    providers_config = payment_config.get('providers', {})
    provider_conf = providers_config.get(provider_name, {})

    if not provider_conf.get('enabled', False) and provider_name != 'manual':
        # Fall back to manual if requested provider isn't enabled
        sys.stderr.write(
            f"[PAYMENTS] Provider '{provider_name}' not enabled, falling back to manual\n")
        provider_name = 'manual'
        provider_conf = providers_config.get('manual', {'enabled': True})

    cls = PROVIDER_CLASSES.get(provider_name)
    if cls is None:
        raise ValueError(
            f"Unknown payment provider: {provider_name}. "
            f"Available: {', '.join(PROVIDER_CLASSES.keys())}")

    inst = cls(provider_conf)
    return (provider_name, inst) if with_name else inst


def get_enabled_providers():
    """Return list of enabled payment provider info dicts."""
    from flask import current_app
    payment_config = current_app.config['_helpers']['config'].get('payment', {})
    providers_config = payment_config.get('providers', {})

    enabled = []
    for name, conf in providers_config.items():
        if conf.get('enabled', False):
            cls = PROVIDER_CLASSES.get(name)
            if cls:
                inst = cls(conf)
                info = inst.get_display_info()
                info['name'] = name
                info['fields'] = inst.get_checkout_fields()
                enabled.append(info)

    return enabled


# =========================================================================
#  WEBHOOK ROUTE (generic -- dispatches to active provider)
# =========================================================================

@payments_bp.route('/api/payment/webhook', methods=['POST'])
def payment_webhook():
    """Webhook endpoint for the ACTIVE provider.

    1. authenticate (provider.verify_webhook: Stripe signature / stub secret)
    2. dedupe on event id (processed_events)
    3. mark an order paid only if status, amount, currency and session match
    """
    from flask import current_app
    helpers = current_app.config['_helpers']
    client_cfg = helpers['config']
    raw_body = request.get_data(cache=True)

    provider_name, provider = get_payment_provider(with_name=True)
    try:
        event = provider.verify_webhook(request, raw_body, client_cfg)
    except WebhookAuthError as e:
        sys.stderr.write(f"[PAYMENTS] webhook rejected ({provider_name}): {e}\n")
        return jsonify({'error': 'unauthorized'}), 400
    if not isinstance(event, dict):
        return jsonify({'error': 'bad event'}), 400

    db = helpers['get_db']()
    try:
        event_id = str(event.get('id') or '')
        if not event_id:
            return jsonify({'error': 'event id required'}), 400
        cur = db.execute(
            "INSERT OR IGNORE INTO processed_events (source, event_id, received_at) "
            "VALUES (?, ?, ?)",
            (f'payment:{provider_name}', event_id, datetime.now().isoformat()))
        if cur.rowcount == 0:
            db.rollback()
            return jsonify({'ok': True, 'duplicate': True}), 200

        result = provider.handle_webhook(event) or {}
        order_id = result.get('order_id')
        note = 'ignored'
        if order_id:
            order = db.execute(
                "SELECT id, total, status, payment_ref FROM orders WHERE id = ?",
                (order_id,)).fetchone()
            if not order:
                note = 'no such order'
            elif result.get('status') == 'completed':
                expected_cents = int(round(float(order['total']) * 100))
                problems = []
                if result.get('payment_status') != 'paid':
                    problems.append('payment_status is not paid')
                if result.get('amount_total') != expected_cents:
                    problems.append('amount mismatch')
                if result.get('currency') != result.get('expected_currency'):
                    problems.append('currency mismatch')
                if order['payment_ref'] and result.get('payment_ref') != order['payment_ref']:
                    problems.append('session does not match order')
                if problems:
                    sys.stderr.write(f"[PAYMENTS] NOT marking {order_id} paid: "
                                     f"{', '.join(problems)}\n")
                    note = 'not applied'
                else:
                    db.execute(
                        "UPDATE orders SET status = 'completed', payment_ref = ? "
                        "WHERE id = ?", (result.get('payment_ref') or '', order_id))
                    note = 'paid'
            elif result.get('status') == 'failed':
                db.execute(
                    "UPDATE orders SET status = 'failed' WHERE id = ? AND status "
                    "IN ('pending', 'payment_error')", (order_id,))
                note = 'failed'
        db.commit()
        return jsonify({'ok': True, 'result': note}), 200

    except Exception as e:
        db.rollback()
        sys.stderr.write(f"[PAYMENTS] Webhook error: {type(e).__name__}: {e}\n")
        return jsonify({'error': 'internal error'}), 500


# =========================================================================
#  ADMIN: Payment provider info page
# =========================================================================

@payments_bp.route('/admin/payments')
def admin_payments():
    if not _is_admin():
        return redirect(url_for('admin_login'))

    from flask import current_app
    payment_config = current_app.config['_helpers']['config'].get('payment', {})
    active = payment_config.get('active_provider', 'manual')
    providers = payment_config.get('providers', {})

    return render_template('admin/payments.html',
                           active_provider=active,
                           providers=providers,
                           provider_classes=list(PROVIDER_CLASSES.keys()))


# =========================================================================
#  MODULE REGISTRATION
# =========================================================================

def get_schema():
    """No additional schema needed -- orders table is in ecommerce module."""
    return ""


def get_nav_items():
    return [
        {'label': 'Payments', 'endpoint': 'payments.admin_payments',
         'match': 'payments.admin_payment'},
    ]


def get_metrics(db):
    """Payment metrics only make sense if ecommerce is also enabled."""
    metrics = []
    try:
        completed = db.execute(
            "SELECT COUNT(*) as c FROM orders WHERE status = 'completed'"
        ).fetchone()['c']
        metrics.append({'label': 'Completed Payments', 'value': completed})
    except Exception:
        pass  # orders table may not exist if ecommerce not enabled
    return metrics
