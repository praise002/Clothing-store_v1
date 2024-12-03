from django.shortcuts import redirect, render
from django.views import View
from django.utils import timezone

from apps.accounts.mixins import LoginRequiredMixin
from apps.coupons.forms import CouponApplyForm
from apps.coupons.models import Coupon, CouponUsage
from django.core.exceptions import ValidationError


class CouponApply(LoginRequiredMixin, View):
    def post(self, request):
        now = timezone.now()
        form = CouponApplyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            try:
                coupon = Coupon.objects.get(
                    code__iexact=code,
                    valid_from__lte=now,
                    valid_to__gte=now,
                    active=True,
                )
                request.session["coupon_id"] = coupon.id
            except Coupon.DoesNotExist:
                request.session["coupon_id"] = None
                raise ValidationError("Invalid or expired coupon.")

            # Ensure user hasn't already redeemed this coupon
            if CouponUsage.objects.filter(
                profile=request.user.profile, coupon=coupon
            ).exists():
                raise ValidationError("You have already used this coupon.")

            return redirect("cart:cart_detail")
