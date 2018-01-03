class ProductionElement:
    def __init__(self, product, quantity, target):
        self.product = product
        self.quantity = quantity
        self.target = target

    def __str__(self):
        return "[" + str(self.product.name) + ":" + str(self.quantity) + ":" + str(self.target) + "]"
