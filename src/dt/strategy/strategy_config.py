"""
Configuration for Hypothesis strategy defaults.

This file defines the default strategies used by StrategySynthesizer
for generating test inputs. You can customize these values to control
the range and characteristics of generated test data.
"""

from typing import Dict, Any, Callable
from hypothesis import strategies as st


class StrategyConfig:
    """
    Configuration class for Hypothesis strategy defaults.

    Modify the values in this class to customize test generation behavior.
    """

    # Integer strategy configuration
    INT_MIN_VALUE = -50
    INT_MAX_VALUE = 50

    # Float strategy configuration
    FLOAT_MIN_VALUE = -50.0
    FLOAT_MAX_VALUE = 50.0
    FLOAT_ALLOW_NAN = False
    FLOAT_ALLOW_INFINITY = False

    # String strategy configuration
    STRING_MAX_SIZE = 10

    # Container strategy configuration
    LIST_MAX_SIZE = 10
    SET_MAX_SIZE = 10
    DICT_MAX_SIZE = 10
    TUPLE_MAX_SIZE = 5

    # Keyword hint configurations (for backward compatibility)
    POSITIVE_INT_MIN = 1
    POSITIVE_INT_MAX = 100
    KEYWORD_STRING_MAX_SIZE = 20
    KEYWORD_FLOAT_MIN = -100.0
    KEYWORD_FLOAT_MAX = 100.0

    @classmethod
    def get_registry(cls) -> Dict[Any, Callable[[], st.SearchStrategy]]:
        """
        Build the strategy registry from configuration values.

        Returns:
            Dictionary mapping types to strategy factories
        """
        return {
            int: lambda: st.integers(
                min_value=cls.INT_MIN_VALUE, max_value=cls.INT_MAX_VALUE
            ),
            float: lambda: st.floats(
                min_value=cls.FLOAT_MIN_VALUE,
                max_value=cls.FLOAT_MAX_VALUE,
                allow_nan=cls.FLOAT_ALLOW_NAN,
                allow_infinity=cls.FLOAT_ALLOW_INFINITY,
            ),
            str: lambda: st.text(max_size=cls.STRING_MAX_SIZE),
            bool: lambda: st.booleans(),
            Any: lambda: st.one_of(
                st.integers(
                    min_value=cls.INT_MIN_VALUE, max_value=cls.INT_MAX_VALUE
                ),
                st.floats(
                    min_value=cls.FLOAT_MIN_VALUE,
                    max_value=cls.FLOAT_MAX_VALUE,
                    allow_nan=cls.FLOAT_ALLOW_NAN,
                    allow_infinity=cls.FLOAT_ALLOW_INFINITY,
                ),
                st.text(max_size=cls.STRING_MAX_SIZE),
                st.booleans(),
            ),
        }

    @classmethod
    def get_keyword_strategy(cls, keyword: str) -> st.SearchStrategy:
        """
        Get a strategy for a keyword hint.

        Args:
            keyword: The keyword hint (e.g., "positive_int", "string")

        Returns:
            Hypothesis SearchStrategy for the keyword
        """
        keyword_strategies = {
            "positive_int": st.integers(
                min_value=cls.POSITIVE_INT_MIN, max_value=cls.POSITIVE_INT_MAX
            ),
            "string": st.text(max_size=cls.KEYWORD_STRING_MAX_SIZE),
            "list": st.lists(
                st.integers(
                    min_value=cls.INT_MIN_VALUE, max_value=cls.INT_MAX_VALUE
                )
            ),
            "float": st.floats(
                min_value=cls.KEYWORD_FLOAT_MIN,
                max_value=cls.KEYWORD_FLOAT_MAX,
                allow_nan=cls.FLOAT_ALLOW_NAN,
                allow_infinity=cls.FLOAT_ALLOW_INFINITY,
            ),
        }
        return keyword_strategies.get(
            keyword,
            st.integers(
                min_value=cls.INT_MIN_VALUE, max_value=cls.INT_MAX_VALUE
            ),
        )


# You can override the default configuration by creating a custom config class
# and passing it to StrategySynthesizer:
#
# class MyCustomConfig(StrategyConfig):
#     INT_MIN_VALUE = -1000
#     INT_MAX_VALUE = 1000
#     STRING_MAX_SIZE = 50
#
# synthesizer = StrategySynthesizer(config=MyCustomConfig)
