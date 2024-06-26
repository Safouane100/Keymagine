from typing import Optional

from pymongo import MongoClient
from pydantic import BaseModel

from bunnet import Document, Indexed, init_bunnet


class Category(BaseModel):
    name: str
    description: str


class Product(Document):
    name: Indexed(str, unique=True)                          # You can use normal types just like in pydantic
    description: Optional[str] = None
    price: Indexed(float)              # You can also specify that a field should correspond to an index
    category: Category                 # You can include pydantic models as well

    def get(name: str):
        return Product.find_one(Product.name == name).run()
        


# Bunnet uses Pymongo client under the hood 
client = MongoClient("mongodb://localhost:27017")

# Initialize bunnet with the Product document class
init_bunnet(database=client.test, document_models=[Product])

chocolate = Category(name="Chocolate", description="A preparation of roasted and ground cacao seeds.")
# Bunnet documents work just like pydantic models
tonybar = Product(name="Tony's", price=5.95, category=chocolate)
yuckbar = Product(name="Yuck", price=0.95, category=chocolate)
diamondbar = Product(name="Diamond", price=999.99, category=chocolate)
# And can be inserted into the database
print("Tony's price:", tonybar.price)

# You can find documents with pythonic syntax
product = Product.find_one(Product.price < 10).run()
print("Test get:", Product.get("lol"))


# And update them
product.set({Product.name:"Gold bar"})