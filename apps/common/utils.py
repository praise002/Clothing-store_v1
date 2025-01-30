from apps.accounts.models import User
from apps.shop.models import Category, Product

class TestUtil:
    def new_user():
        user_dict = {
            "first_name": "Test",
            "last_name": "Name",
            "email": "test@example.com",
            "password": "testpassword",
        }
        user = User.objects.create_user(**user_dict)
        return user
    
    def verified_user():
        user_dict = {
            "first_name": "Test",
            "last_name": "Verified",
            "email": "testverifieduser@example.com",
            "is_email_verified": True,
            "password": "testpassword",
        }
        user = User.objects.create_user(**user_dict)
        return user
    
    def other_user():
        user_dict = {
            "first_name": "Test",
            "last_name": "Other",
            "email": "testotheruser@example.com",
            "is_email_verified": True,
            "password": "testpassword",
        }
        user = User.objects.create_user(**user_dict)
        return user
    
    def admin_user():
        user_dict = {
            "first_name": "Test",
            "last_name": "Other",
            "email": "testotheruser@example.com",
            "is_email_verified": True,
            "is_staff": True,
            "is_superuser": True,
            "password": "testpassword",
        }
        user = User.objects.create_user(**user_dict)
        return user
    
    def inactive_user():
        user_dict = {
            "first_name": "Test",
            "last_name": "Inactive",
            "email": "testotherinactive@example.com",
            "is_email_verified": True,
            "password": "testpassword",
            "user_active": False,
        }
        user = User.objects.create_user(**user_dict)
        return user
    
    def create_category():
        return Category.objects.create(name="Electronics")
    
    def create_product():
        return Product.objects.create(
            name="Laptop",
            description="Text product",
            price=50.00,
            in_stock=10,
            is_available=True,
            image="/media/photos/2024/09/01/test_image.jpg",  
        )
        
    def create_product_with_category():
        category = Category.objects.create(name="Electronics")
        return Product.objects.create(
            name="Laptop",
            description="Text product",
            price=50.00,
            in_stock=10,
            is_available=True,
            image="/media/photos/2024/09/01/test_image.jpg",
            category=category,
        )
        
        