# Lynette Bishop

![](https://i.ibb.co/52h6qnk/icon004sw.jpg "Lynette Bishop/リネット・ビショップ From Strike Witches")

*[Picture Art: [@chameleonman3](https://twitter.com/chameleonman3)]*

A "Simple" twitter to discord webhook bot:

## Features:

- Outer Link Expansion
- Mobile "compatible" embeds
  - Custom Fantia link expansion
  - Twitter Cards Expansion

## Extending Outer Link Expansion

1. Create a new class, inheriting from `AsyncResolver`
2. add resolver domains to `SITES` in `TwitterResolver`
3. Test [You can run `MiyafujiYoshika.py` directly, be sure to fill the keys and webhook url.]
4. Profit.

## Running

1. Fill in `KEYS` from twitter, you may use `AuthTools` to get your own `access_token` and `access_token_secret`.
2. Install required dependencies from requirements.txt
3. Place your discord bot key.
4. Run the bot
5. Add hooks. there are commands for that
6. Add twitter users.

## Development

- Feel free to PR.
- Main development will be based on my requirements. If you want X feature, you might need to wait.

## Thanks

- `AuthTools` I recall I took it from somewhere on github, but I can't seem to find it anymore.   
If someone knows where the github link has gone to, please let me know in an issue.

## License

- MIT License, `AuthTools` License, I'm not too sure about...