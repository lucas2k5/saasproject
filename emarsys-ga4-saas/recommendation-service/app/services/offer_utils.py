"""Utilitários de cálculo de ofertas — compartilhado entre API e serviços."""


def compute_promo_price(offer_type: str, params: dict, base_price: float) -> float:
    """Calcula o menor preço unitário resultante da promoção."""
    try:
        if offer_type == "DIRECT_DISCOUNT":
            if params.get("discount_type") == "percent":
                return round(base_price * (1 - params["discount_value"] / 100), 2)
            else:  # fixed
                return round(max(0.0, base_price - params["discount_value"]), 2)

        elif offer_type == "TAKE_X_PAY_Y":
            take = params["take"]
            pay = params["pay"]
            return round(base_price * pay / take, 2)

        elif offer_type == "BUY_X_GET_Y":
            return base_price

        elif offer_type == "BUY_X_GET_PRODUCT":
            return base_price

        elif offer_type == "PROGRESSIVE":
            tiers = sorted(params.get("tiers", []), key=lambda t: -t["min_qty"])
            for tier in tiers:
                if 1 >= tier["min_qty"]:
                    return round(base_price * (1 - tier["discount_percent"] / 100), 2)
            return base_price

        elif offer_type == "COMBO":
            discount = params.get("combo_discount_percent")
            if discount:
                return round(base_price * (1 - discount / 100), 2)
            return base_price

        elif offer_type == "CASHBACK":
            return round(base_price * (1 - params.get("cashback_percent", 0) / 100), 2)

    except (KeyError, TypeError, ZeroDivisionError):
        pass
    return base_price
