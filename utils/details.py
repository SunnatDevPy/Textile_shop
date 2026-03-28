from models import Cart, ShopProduct, ShopCategory, Shop, \
    BotUser, OrderItem, Order
from models import ProductTip


async def sum_price_carts(carts: list['Cart']):
    sum_ = 0
    for i in carts:
        sum_ += i.total
    return sum_


async def update_products(products):
    list_ = []
    for i in products:
        shop = await Shop.get(i.shop_id)
        i.shop = shop
        list_.append(i)
    return list_


async def detail_order(order):
    order_items: list['OrderItem'] = await OrderItem.get_order_items(order.id)
    text = ''
    count = 1
    for i in order_items:
        product = await ShopProduct.get(i.product_id)
        text += f"{count}) {product.name} {i.price} x {i.count} = {i.total}\n"
    return f"""
<blockquote>
<b>Buyurtma soni</b>: {order.id}
<b>Mijoz</b>: {order.first_last_name}
<b>Telefon</b>: {order.contact}
<b>To'lov turi</b>: {order.payment}

<b>Mahsulotlar</b>
{text}

<b>Yo'l kira narxi</b>: {order.driver_price}
<b>Umumiy summa</b>: {order.total_sum}
</blockquote>
    """
