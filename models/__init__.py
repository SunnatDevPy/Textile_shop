from models.database import db
from models.products_model import Category, Product, ProductItems, ProductPhoto, ProductDetail, Size, Color, OrderItem, Order, Collection
from models.users import AdminUser, MainPhoto, Country
from models.audit_log import AuditLog

AdminPanelUser = AdminUser