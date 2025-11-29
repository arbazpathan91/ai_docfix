import asyncio
import uuid
import time
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass

# Simulated Database
DB_STORE = {
    "users": {},
    "orders": {},
    "inventory": {}
}

class DatabaseError(Exception):
    """
    Custom exception for database-related errors.
    """

    pass

class AuthError(Exception):
    """
    Custom exception for authentication-related failures.
    """

    pass

@dataclass
class User:
    """
    Represents a user profile with basic identification and authentication
        information.

    Attributes:
        id (str): A unique identifier for the user.
        username (str): The user's chosen username.
        email (str): The user's email address.
        is_active (bool): Indicates if the user account is currently active.
            Defaults to True.
        roles (List[str]): A list of roles assigned to the user, such as
            'admin', 'customer', etc. Defaults to None.
    """

    id: str
    username: str
    email: str
    is_active: bool = True
    roles: List[str] = None

@dataclass
class OrderItem:
    """
    Represents a single item within an order, specifying the product and its
        quantity.

    Args:
        product_id (str): The unique identifier for the product.
        quantity (int): The number of units of the product.
    """

    product_id: str
    quantity: int
    price_per_unit: float

class SecurityContext:
    """
    Initializes the SecurityContext with an authentication token.

    Args:
        token (str): The authentication token to be validated and used for
            user identification.
    """

    def __init__(self, token: str):
        """
        Initializes a new SecurityContext instance.

        Args:
            token (str): The security token associated with the current context.
        """

        self.token = token
        self._user_cache = None

    def validate(self) -> bool:
        """
        Validates the security token associated with the context.

        This method checks if the token is present and meets a minimum length
            requirement, which is essential for subsequent operations that rely
            on a valid token.

        Returns:
            bool: True if the token is valid, False otherwise.
        """

        if not self.token or len(self.token) < 10:
            return False
        return True

    def get_user_id(self) -> Optional[str]:
        """
        Retrieves the user ID from the security token.

        This method first validates the internal token. If valid, it attempts to
            extract
        the user ID from the token string using a mock decoding logic.

        Returns:
            Optional[str]: The user ID if the token is valid and the ID can be
                extracted,
            otherwise None.
        """

        if self.validate():
            # Mock decoding logic
            return self.token.split(":")[0] if ":" in self.token else None
        return None

class InventoryManager:
    """
    Initializes the InventoryManager with a reference to the database.

    This allows the manager to interact with and modify inventory data
        within the simulated database.

    Args:
        db_ref (Dict): A dictionary representing the database, which should
            contain an "inventory" key.
    """

    def __init__(self, db_ref: Dict):
        """
        Initializes the InventoryManager with a reference to the database.

        This allows the manager to interact directly with the inventory data
            stored within the provided database structure.

        Args:
            db_ref (Dict): A dictionary representing the database, expected to
                contain an "inventory" key.
        """

        self.db = db_ref

    def check_stock(self, product_id: str, quantity: int) -> bool:
        """
        Checks if a specified quantity of a product is available in the
            inventory.

        Args:
            product_id (str): The unique identifier of the product to check.
            quantity (int): The desired quantity of the product.

        Returns:
            bool: True if the product exists and the available quantity is
                greater than or
            equal to the requested quantity, False otherwise.
        """

        item = self.db["inventory"].get(product_id)
        if not item:
            return False
        return item["qty"] >= quantity

    def reserve(self, product_id: str, quantity: int) -> bool:
        """
        Attempts to reserve a specified quantity of a product from the
            inventory.

        This method first checks if there is sufficient stock available for the
            given product. If enough stock exists, it reduces the quantity of
            that product in the database's inventory.

        Args:
            product_id (str): The unique identifier of the product to reserve.
            quantity (int): The amount of the product to reserve.

        Returns:
            bool: True if the reservation was successful (i.e., sufficient stock
                was available and reduced), False otherwise.
        """

        if self.check_stock(product_id, quantity):
            self.db["inventory"][product_id]["qty"] -= quantity
            return True
        return False

    def release(self, product_id: str, quantity: int) -> None:
        """
        Releases (returns) a specified quantity of a product back into the
            inventory.

        This method is typically called to reverse a previous reservation or to
            restock items that were not successfully purchased. It only modifies
            the quantity if the product exists in the inventory.

        Args:
            product_id (str): The unique identifier of the product to release.
            quantity (int): The amount of the product to add back to stock.
        """

        if product_id in self.db["inventory"]:
            self.db["inventory"][product_id]["qty"] += quantity

class PaymentGateway:
    """
    Manages payment processing interactions with an external gateway.

    This class provides methods to process payments, simulating an
        interaction with a third-party payment service. It holds
        configuration details like an API key.
    """

    _api_key: str = "sk_test_12345"

    @classmethod
    def configure(cls, key: str):
        """
        Configure the PaymentGateway's API key.

        This method allows setting the API key used for processing payments,
            overriding the default test key.

        Args:
            key (str): The new API key to be used for payment processing.
        """

        cls._api_key = key
        
    @staticmethod
    async def process_payment(amount: float, currency: str = "USD") -> Dict[str, str]:
        """
        Simulates processing a payment through an external gateway.

        This method introduces a simulated network latency and generates a
            unique transaction ID for successful payments. It's designed to
            mimic the behavior of a real payment service.

        Args:
            amount (float): The monetary amount to be processed.
            currency (str): The currency code for the payment (e.g., "USD").
                Defaults to "USD".

        Returns:
            Dict[str, str]: A dictionary containing the payment status,
                transaction ID, and timestamp.

        Raises:
            ValueError: If the `amount` is less than or equal to zero.
        """

        # Simulate network latency
        await asyncio.sleep(0.5)
        
        if amount <= 0:
            raise ValueError("Invalid amount")
        
        tx_id = hashlib.sha256(f"{time.time()}{amount}".encode()).hexdigest()
        return {"status": "success", "tx_id": tx_id, "timestamp": str(datetime.now())}

class OrderProcessor:
    """
    Initializes the OrderProcessor with an inventory manager.

    Args:
        inventory (InventoryManager): An instance of InventoryManager to
            handle stock operations.
    """

    def __init__(self, inventory: InventoryManager):
        """
        Initializes the OrderProcessor with an inventory manager and an empty
            order queue.

        Args:
            inventory (InventoryManager): An instance of InventoryManager to
                handle stock operations.
        """

        self.inv = inventory
        self.queue: List[Tuple[str, List[OrderItem]]] = []
        self._is_running = False

    async def start_worker(self):
        """
        Starts an asynchronous worker that continuously processes orders from
            the internal queue.

        This method sets a flag to `True` and enters an infinite loop, checking
            for new orders in the queue. If orders are present, it processes
            them; otherwise, it pauses briefly. The loop continues until
            `stop_worker` is called.
        """

        self._is_running = True
        while self._is_running:
            if self.queue:
                order_id, items = self.queue.pop(0)
                await self._handle_order(order_id, items)
            else:
                await asyncio.sleep(1)

    def stop_worker(self):
        """
        Stop the background worker for processing orders.

        This method sets an internal flag to `False`, which causes the
            `start_worker` asynchronous loop to terminate gracefully after its
            current iteration or next check.
        """

        self._is_running = False

    def submit_order(self, user: User, items: List[OrderItem]) -> str:
        """
        Submits a new order for processing.

        This method performs initial validations, creates a pending order record
            in the database,
        and adds the order to an internal queue for asynchronous fulfillment by
            a worker.

        Args:
            user (User): The user placing the order.
            items (List[OrderItem]): A list of items included in the order,
            specifying product IDs, quantities, and prices.

        Returns:
            str: The unique identifier for the newly submitted order.

        Raises:
            AuthError: If the provided user is not active.
            ValueError: If any item in the order is out of stock.
        """

        if not user.is_active:
            raise AuthError("User inactive")

        order_id = str(uuid.uuid4())
        
        # Pre-validation
        total = 0.0
        for item in items:
            if not self.inv.check_stock(item.product_id, item.quantity):
                raise ValueError(f"Out of stock: {item.product_id}")
            total += item.quantity * item.price_per_unit

        # Create pending order
        DB_STORE["orders"][order_id] = {
            "user_id": user.id,
            "items": items,
            "total": total,
            "status": "pending",
            "created_at": datetime.now()
        }
        
        self.queue.append((order_id, items))
        return order_id

    async def _handle_order(self, order_id: str, items: List[OrderItem]):
        print(f"Processing order {order_id}...")
        
        # 1. Reserve Inventory
        reserved_items = []
        try:
            for item in items:
                if self.inv.reserve(item.product_id, item.quantity):
                    reserved_items.append(item)
                else:
                    raise Exception("Inventory race condition")

            # 2. Charge Payment
            order_data = DB_STORE["orders"][order_id]
            payment_result = await PaymentGateway.process_payment(order_data["total"])
            
            if payment_result["status"] == "success":
                DB_STORE["orders"][order_id]["status"] = "completed"
                DB_STORE["orders"][order_id]["tx_id"] = payment_result["tx_id"]
                print(f"Order {order_id} completed successfully.")
            else:
                raise Exception("Payment failed")

        except Exception as e:
            print(f"Order {order_id} failed: {e}")
            DB_STORE["orders"][order_id]["status"] = "failed"
            # Rollback inventory
            for item in reserved_items:
                self.inv.release(item.product_id, item.quantity)

async def main_simulation():
    """
    Simulates the entire order processing workflow.

    This function sets up initial inventory data, creates an
        `InventoryManager` and `OrderProcessor`, starts the order processing
        worker, simulates a user submitting an order, and then monitors the
        order's status. It demonstrates the asynchronous nature of the
        system.
    """

    # Setup Data
    DB_STORE["inventory"]["p1"] = {"name": "Laptop", "qty": 10}
    DB_STORE["inventory"]["p2"] = {"name": "Mouse", "qty": 50}

    inv_mgr = InventoryManager(DB_STORE)
    processor = OrderProcessor(inv_mgr)
    # Start Background Worker
    worker_task = asyncio.create_task(processor.start_worker())

    # Simulate User Action
    u1 = User(id="u1", username="john_doe", email="john@example.com")
    
    cart = [
        OrderItem("p1", 1, 999.99),
        OrderItem("p2", 2, 25.50)
    ]

    try:
        order_id = processor.submit_order(u1, cart)
        print(f"Order submitted: {order_id}")
    except Exception as e:
        print(f"Submission error: {e}")

    # Let the worker process
    await asyncio.sleep(3)
    
    # Check status
    print("Final Order Status:", DB_STORE["orders"][order_id]["status"])
    
    processor.stop_worker()
    await worker_task

if __name__ == "__main__":
    asyncio.run(main_simulation())