from core import models, search, utils


class IngredientError(Exception):
    """Exception raised when parsing ingredient fails."""

    def __init__(self, to_parse, message):
        self.to_parse = to_parse
        self.message = message


class Ingredient():
    """Parses and stores data about an ingredient.
    
    Class which parses ingredient and stores data about it's weight, amount, nutrition, etc..
    Raises IngredientError if parser couldn't match a Food in database or Food doesn't have any FoodWeight to be selected.

    Example usage:
    >>> ing = Ingredient("100 g of chicken breast")
    >>> ing.amount, ing.unit, ing.measurement, ing.name
    (100.0, 'g', '', 'chicken breast')
    >>> ing.weight, ing.matched_food
    (100.0, <Food: #5057 Chicken, broilers or fryers, breast, meat and skin, raw>)
    >>> ing.energy, ing.protein, ing.fat
    (172.0, 20.85, 9.25)

    Attributes:
    :amount - amount of weight
    :unit   - unit (if parsed)
    :measurement - measurement (if parsed or no unit) e.g. slice, stick, batch, etc..
    :name   - name of ingredient
    :matched_food - Food object from database
    :weight - weight in grams
    """

    def __init__(self, to_parse: str):
        self.amount, self.unit, self.measurement, self.name = search.parse_ingredient(
            to_parse
        ).values()
        self.matched_food = search.match_one_food(self.name)
        if not self.matched_food:
            raise IngredientError(to_parse, f"Couldn't match a food object.")
        if self.unit:
            self.weight = self.amount * utils.unit_to_grams[self.unit]
        else:
            self.weight = self.get_weight()

    def get_weight(self):
        """
        Returns weight (in grams).
        """
        if not self.matched_food.weight.exists():
            raise IngredientError(
                self.matched_food, f"This food doesn't have any FoodWeight objects."
            )
        matched_weight = search.match_one_weight(self.matched_food, self.measurement)
        return float(matched_weight.weight) * (
            self.amount / float(matched_weight.amount)
        )

    def __repr__(self):  # pragma: no cover
        return f"{self.weight:.2f} g of {self.matched_food.desc_long}"

    def calc_nutrient(self, tagname: str) -> float:
        """
        Calculates nutrient amount for ingredient's weight

        Args: 
            tagname: International Network of Food Data Systems tagname
        Returns: 
            Amount of nutrient (in it's corresponding unit) for self.weight 
        """
        nutrient = self.get_nutrient_by_tagname(tagname)
        if not nutrient:
            return None
        return float(nutrient.value) / 100 * self.weight

    def get_nutrient_by_tagname(self, tagname: str) -> models.FoodNutrition:
        """
        Returns nutrient by tagname (if exists in database)
        """
        try:
            return self.matched_food.nutrition.get(tagname=tagname)
        except models.FoodNutrition.DoesNotExist:
            return None

    @property
    def energy(self):
        return self.calc_nutrient("ENERC_KCAL")

    @property
    def protein(self):
        return self.calc_nutrient("PROCNT")

    @property
    def fat(self):
        return self.calc_nutrient("FAT")

    @property
    def fat_sat(self):
        return self.calc_nutrient("FASAT")

    @property
    def fat_poly(self):
        return self.calc_nutrient("FAPU")

    @property
    def fat_mono(self):
        return self.calc_nutrient("FAMS")

    @property
    def carb(self):
        return self.calc_nutrient("CHOCDF")

    @property
    def sugar(self):
        return self.calc_nutrient("SUGAR")

    @property
    def chol(self):
        return self.calc_nutrient("CHOLE")

    @property
    def sodium(self):
        return self.calc_nutrient("NA")

    @property
    def potas(self):
        return self.calc_nutrient("K")

    @property
    def fiber(self):
        return self.calc_nutrient("FIBTG")


def calculate_total_nutrition(ingredients: list) -> dict:
    """Returns total nutrition for list of ingredients.
    
    Values are rounded with 2 digit precision.

    Args:
        ingredients: list of Ingredient objects.
    Returns:
        Dictionary with nutrition name as a key and tuple of amount and unit as value, e.g.
        {
            'PROTEIN': (127.21, 'g'),
            'FAT': (124.13, 'g'),
            ...
        }
    """
    total_nutrition = {
        # Big 4
        "ENERGY": 0,
        "FAT": 0, 
        "PROTEIN": 0, 
        "CARB": 0,
        # The rest
        # "FAT_SAT": 0,
        # "FAT_POLY": 0,
        # "FAT_MONO": 0,
        "SUGAR": 0,
        "CHOLE": 0,
        "SODIUM": 0,
        "POTAS": 0,
        "FIBER": 0,
    }
    to_tagname = {
        "ENERGY": "ENERC_KCAL", 
        "FAT": "FAT", 
        "PROTEIN": "PROCNT", 
        "CARB": "CHOCDF",
        # The rest
        "FAT_SAT": "FASAT",
        "FAT_POLY": "FAPU",
        "FAT_MONO": "FAMS",
        "SUGAR": "SUGAR",
        "CHOLE": "CHOLE",
        "SODIUM": "NA",
        "POTAS": "K",
        "FIBER": "FIBTG",
    }
    units = {
        "ENERGY": "kcal", 
        "FAT": "g", 
        "PROTEIN": "g", 
        "CARB": "g",
        "FAT_KCAL": "kcal",
        "PROTEIN_KCAL": "kcal",
        "CARB_KCAL": "kcal",
        "FAT_SAT": "g",
        "FAT_POLY": "g",
        "FAT_MONO": "g",
        "SUGAR": "g",
        "CHOLE": "mg",
        "SODIUM": "mg",
        "POTAS": "mg",
        "FIBER": "g",
    }
    for i in ingredients:
        for n in total_nutrition:
            calculated = i.calc_nutrient(to_tagname[n])
            if calculated:
                total_nutrition[n] += calculated
    # Round results and create a tuple with value and unit
    for k, v in total_nutrition.items():
        total_nutrition[k] = (round(v, 2), units[k])
    

    return total_nutrition


def calculate_serving_nutrition(total_nutrition: dict, servings: int) -> dict:
    """Returns nutrition per serving for total nutrition.
    
    Values are rounded with 2 digit precision.

    Args:
        total_nutrition: dictionary calculated by calculate_total_nutrition().
        servings: count of servings
    Returns:
        Dictionary with nutrition name as a key and tuple of amount and unit as value, e.g.
        {
            'ENERGY': (1237.21, 'kcal'),
            'FAT': (124.13, 'g'),
            ...
        }
    """
    return {k: (round(t[0] / servings, 2), t[1]) for k, t in total_nutrition.items()}
