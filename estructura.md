### Tipos:
    - tipo de video (post_categories.category_type):
        - Youtube: videos, shorts.
        - Tiktok: videos(feed).
        - Instagram: feed (img), reels, stories, highlights, tagged.
        - Otros: videos y shorts.

  >nota: Importante, verifica FINAL_DATABASE_SCHEMA.md para saber todos los detalles.

## Como se mostrara en el frontend:
Un creador puede tener videos en varias plataformas por lo que su perfil debe estar organizado. Los tabs y subtabs van juntos

    - Cuentas:
        - Tab: `All`
        - Tab: `Plataformas`
            - Youtube:
                - SubTabs: All, Videos, Shorts, Listas.
            - Tiktok:
                - SubTabs: All, Videos, Lista Saved, Lista Liked.
            - Instagram:
                - SubTabs: All, Reels, Stories, Highlights, Tagged, Lista Saved.
            - *Otras:
                - SubTabs: All, videos, shorts.