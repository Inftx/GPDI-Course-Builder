class AIProvider:

    """
    Base AI Provider.

    Every AI service will inherit from this.
    """

    def generate(
        self,
        prompt
    ):
        raise NotImplementedError(
            "Provider must implement generate()."
        )
