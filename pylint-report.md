******\******* Module recipes
recipes.py:79:0: R0913: Too many arguments (8/5) (too-many-arguments)
recipes.py:79:0: R0917: Too many positional arguments (8/5) (too-many-positional-arguments)
recipes.py:118:0: R0913: Too many arguments (8/5) (too-many-arguments)
recipes.py:118:0: R0917: Too many positional arguments (8/5) (too-many-positional-arguments)
******\******* Module validator
validator.py:78:0: R0911: Too many return statements (7/6) (too-many-return-statements)
validator.py:108:0: R0911: Too many return statements (8/6) (too-many-return-statements)

---

Your code has been rated at 9.91/10

Yhteenveto
- services.recipe_service, liian paljon argumentteja funktioihin mutta luokan tai objektin tekeminen refaktorointina vaikuttaa overkillilta
- validator liian monta return statementtia kun validoidaan montaa eri asiaa validaattorissa, ei ylity paljolla niin en monimutkaistattanut lisäfunktioilla
