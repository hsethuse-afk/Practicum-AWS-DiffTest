def largest_prime_factor(n: int):
    """Return the largest prime factor of n. Assume n > 1 and is not a prime.
    >>> largest_prime_factor(13195)
    29
    >>> largest_prime_factor(2048)
    2
    """
    if n <= 1:
        raise ValueError("n must be greater than 1")
    max_factor = 1
    # Remove factors of 2
    while n % 2 == 0:
        max_factor = 2
        n //= 2
    # Check odd factors
    f = 3
    while f * f <= n:
        while n % f == 0:
            max_factor = f
            n //= f
        f += 2
    # If remaining n is > 1 then it is a prime factor larger than sqrt(original n)
    if n > 1:
        max_factor = n
    return int(max_factor)
