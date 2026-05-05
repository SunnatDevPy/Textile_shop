from models.database import db
from models.products_model import Category, Product, ProductItems, ProductPhoto, ProductDetail, Size, Color, OrderItem, Order, Collection, PaymentReceipt
from models.users import AdminUser, MainPhoto, Country
from models.audit_log import AuditLog
from models.stock_movements import StockMovement
from models.bot_settings import BotSettings

AdminPanelUser = AdminUser