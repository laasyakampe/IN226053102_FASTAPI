from fastapi import FastAPI, Query, Response, status, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()

# temporary product list
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},  # product is out of stock
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
]

# lists to store cart and orders
orders = []
order_counter = 1
cart = []


# find product using id
def find_product(product_id: int):
    for p in products:
        if p["id"] == product_id:
            return p
    return None


# calculate subtotal price
def calculate_total(product: dict, quantity: int):
    return product["price"] * quantity


# model for checkout request
class CheckoutRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    delivery_address: str = Field(..., min_length=10)


# home endpoint
@app.get("/")
def home():
    return {"message": "FastAPI Is Working"}


# add product to cart or update quantity
@app.post("/cart/add")
def add_to_cart(
    product_id: int = Query(..., description="Product ID"),
    quantity: int = Query(1, description="Quantity")
):

    # get product from list
    product = find_product(product_id)

    # return error if product not found
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # return error if product is out of stock
    if not product["in_stock"]:
        raise HTTPException(status_code=400, detail=f"{product['name']} is out of stock")

    # quantity must be at least 1
    if quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")

    # update quantity if product already in cart
    for item in cart:
        if item["product_id"] == product_id:
            item["quantity"] += quantity
            item["subtotal"] = calculate_total(product, item["quantity"])

            return {
                "message": "Cart updated",
                "cart_item": item
            }

    # create new cart item
    cart_item = {
        "product_id": product_id,
        "product_name": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "subtotal": calculate_total(product, quantity)
    }

    # add item to cart
    cart.append(cart_item)

    return {
        "message": "Added to cart",
        "cart_item": cart_item
    }


# view cart details
@app.get("/cart")
def view_cart():

    # show message if cart is empty
    if not cart:
        return {"message": "Cart is empty", "items": [], "grand_total": 0}

    # calculate total cart price
    grand_total = sum(item["subtotal"] for item in cart)

    return {
        "items": cart,
        "item_count": len(cart),
        "grand_total": grand_total
    }


# checkout cart and create orders
@app.post("/cart/checkout")
def checkout(checkout_data: CheckoutRequest, response: Response):

    global order_counter

    # do not allow checkout if cart is empty
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty — add items first")

    placed_orders = []
    grand_total = 0

    # create order for each cart item
    for item in cart:

        order = {
            "order_id": order_counter,
            "customer_name": checkout_data.customer_name,
            "product": item["product_name"],
            "quantity": item["quantity"],
            "delivery_address": checkout_data.delivery_address,
            "total_price": item["subtotal"],
            "status": "confirmed"
        }

        orders.append(order)
        placed_orders.append(order)

        grand_total += item["subtotal"]
        order_counter += 1

    # clear cart after checkout
    cart.clear()

    response.status_code = status.HTTP_201_CREATED

    return {
        "message": "Checkout successful",
        "orders_placed": placed_orders,
        "grand_total": grand_total
    }


# remove product from cart
@app.delete("/cart/{product_id}")
def remove_from_cart(product_id: int, response: Response):

    # find item in cart
    for item in cart:
        if item["product_id"] == product_id:
            cart.remove(item)
            return {"message": f"{item['product_name']} removed from cart"}

    # return error if item not in cart
    response.status_code = status.HTTP_404_NOT_FOUND
    return {"error": "Product not in cart"}


# view all orders
@app.get("/orders")
def get_orders():
    return {
        "orders": orders,
        "total_orders": len(orders)
    }
