from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from models import SessionLocal, engine, Product
from parser import scrape_products

app = FastAPI()
# base_url = https://at-store.ru/internet-shop/kupit_apple_iphone/

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/scrape/")
def scrape(base_url: str, db: Session = Depends(get_db)):
    products = scrape_products(base_url)
    for title, price in products:
        db.add(Product(title=title, price=price))
    db.commit()
    return {"message": "Products scraped and added to database."}

@app.get("/products/")
def get_products(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    products = db.query(Product).offset(skip).limit(limit).all()
    return products

@app.put("/products/{product_id}")
def update_product(product_id: int, title: str, price: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.title = title
    product.price = price
    db.commit()
    return product

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return {"detail": "Product deleted"}