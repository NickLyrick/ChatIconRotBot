"""This module contains the PlatinumRecord class"""


class PlatinumRecord:
    """PlatinumRecord is class for record of platinum

    Args:
        hunter (str): name of the hunter
        game (str): name of the game
        photo_id (str): id of the photo
        platform (str): platform on which the platinum was achieved
        user_id: Telegram User ID

    Attributes:
        hunter (str): name of the hunter
        game (str): name of the game
        photo_id (str): id of the photo
        platform (str): platform on which the platinum was achieved
        user_id: Telegram User ID

    Methods:
        __init__(self, hunter: str, game: str, photo_id: str, platform: str): initializes the object
        __str__(self) -> str: returns a string representation of the object
        __repr__(self) -> str: returns the representation of the object
        __eq__(self, other: PlatinumRecord) -> bool: returns True if both objects are equal

    """

    def __init__(self, hunter: str, game: str, photo_id: str, platform: str, user_id: int):
        """__init__ initializes the object

        Args:
            hunter (str): name of the hunter
            game (str): name of the game
            photo_id (str): id of the photo
            platform (str): platform on which the platinum was achieved
            user_id: Telegram User ID

        """
        super().__init__()
        self.hunter = hunter
        self.game = game
        self.photo_id = photo_id
        self.platform = platform
        self.user_id = user_id

    def __str__(self) -> str:
        """__str__ returns a string representation of the object

        Returns:
            str: string representation of the object

        """
        return f"{self.hunter} {self.game} {self.platform}"

    def __repr__(self) -> str:
        """__repr__ returns the representation of the object

        Returns:
            str: representation of the object

        """
        return (
            f"PlatinumRecord(hunter={self.hunter}, game={self.game}, "
            f"photo_id={self.photo_id}, platform={self.platform})"
        )

    def __eq__(self, other: "PlatinumRecord") -> bool:
        """__eq__ returns True if both objects are equal

        Args:
            other (PlatinumRecord): object to compare with

        Returns:
            bool: True if both objects are equal, False otherwise

        """
        return (
            (self.user_id == other.user_id)
            and (self.game == other.game)
            and (self.platform == other.platform)
        )
