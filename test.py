def fibonacci(n):
    """
    This function generates the Fibonacci sequence up to a specified number of terms.
    """
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    else:
        list_fib = [0, 1]
        while len(list_fib) < n:
            next_fib = list_fib[-1] + list_fib[-2]
            list_fib.append(next_fib)
        return list_fib

if __name__ == '__main__':
    # Example: Generate the first 10 terms of the Fibonacci sequence
    num_terms = 10
    fib_sequence = fibonacci(num_terms)
    print(f"The first {num_terms} terms of the Fibonacci sequence are: {fib_sequence}")

    # Example: Generate the first 15 terms of the Fibonacci sequence
    num_terms = 15
    fib_sequence = fibonacci(num_terms)
    print(f"The first {num_terms} terms of the Fibonacci sequence are: {fib_sequence}")
