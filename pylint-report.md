************* Module services.recipe_service
services/recipe_service.py:79:0: R0913: Too many arguments (8/5) (too-many-arguments)
services/recipe_service.py:79:0: R0917: Too many positional arguments (8/5) (too-many-positional-arguments)
services/recipe_service.py:118:0: R0913: Too many arguments (8/5) (too-many-arguments)
services/recipe_service.py:118:0: R0917: Too many positional arguments (8/5) (too-many-positional-arguments)
************* Module utils.validator
utils/validator.py:78:0: R0911: Too many return statements (7/6) (too-many-return-statements)
utils/validator.py:108:0: R0911: Too many return statements (8/6) (too-many-return-statements)

------------------------------------------------------------------
Your code has been rated at 9.92/10 (previous run: 9.90/10, +0.01)

# Yhteenveto

- services.recipe_service, liian paljon argumentteja funktioihin mutta luokan tai objektin tekeminen refaktorointina vaikuttaa overkillilta
- utils.validator liian monta return statementtia kun validoidaan montaa eri asiaa validaattorissa, ei ylity paljolla niin en monimutkaistattanut lisäfunktioilla