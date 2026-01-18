from . import db
from .models import Product, WarehouseItem
#this seed is to make it easier instead of inserting products and manifacturers each time we reset database
def seed_products():

    # clear tables
    WarehouseItem.query.delete()
    Product.query.delete()
    db.session.commit()

    products = [
        ("Rice 5kg", 8.5, "200001", 5, 1, "rice.jpg", 40),
        ("Flour 1kg", 1.8, "200002", 10, 1, "flour.jpg", 46),
        ("Pasta Pack", 1.3, "200003", 5, 1, "pasta.jpg", 25),
        ("Olive Oil 1L", 9.9, "200004", 15, 2, "olive_oil.jpg", 15),
        ("Sunflower Oil 1L", 6.5, "200005", 5, 2, "sunflower_oil.jpg", 29),
        ("Tomato Sauce", 1.0, "200006", 0, 2, "tomato.jpg", 60),
        ("Chicken Breast 1kg", 7.8, "200007", 0, 3, "chicken.jpg", 18),
        ("Frozen Fries", 3.1, "200008", 10, 3, "fries.jpg", 35),
        ("Tuna Can", 2.1, "200009", 0, 3, "tuna.jpg", 45),
        ("Eggs 12pcs", 3.6, "200010", 5, 4, "eggs.jpg", 50),
    ]

    for name, price, barcode, disc, man, img, qty in products:
        p = Product(
            Name=name,
            Price=price,
            Barcode=barcode,
            Discount_Percent=disc,
            Man_ID=man,
            Image=img
        )
        db.session.add(p)
        db.session.flush()   # get Product_ID

        w = WarehouseItem(
            Product_ID=p.Product_ID,
            Quantity=qty
        )
        db.session.add(w)

    db.session.commit()
