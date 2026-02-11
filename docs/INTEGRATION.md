# Integration into other Django projects

## Allauth compatibility

This app does not create authentication tables and does not ship its own user model.

It references the project user model via `settings.AUTH_USER_MODEL`.

So:
- Projects using Django default auth → works.
- Projects using Allauth + custom user model → works.
- No duplicated Allauth tables.

## URL mounting

Mount under any prefix, e.g.:

- `/utilities/`
- `/dashboard/utilities/`
- `/master/utilities/`

## Master dashboard integration

If you have a master dashboard project, install this app as a dependency and mount its URLs. Data remains scoped per user; you can add a “portfolio” layer (property/account grouping) later.
