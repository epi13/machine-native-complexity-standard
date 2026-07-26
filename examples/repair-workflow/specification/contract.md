# Bounded index contract

Return `items[index]` only for `0 <= index < len(items)`; otherwise raise
`IndexError`. Empty input is valid and always rejects.
