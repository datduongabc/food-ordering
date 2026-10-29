"""seed menu catalog

Ports the categories, branches and dishes from the PHP app's config/init_postgres.sql.

Revision ID: 3b1c7e9a0d52
Revises: 9f4618e2c491
Create Date: 2026-10-29 02:20:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "3b1c7e9a0d52"
down_revision: str | None = "9f4618e2c491"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CATEGORIES = [
    {"name": "Starters", "slug": "starters"},
    {"name": "Main Dishes", "slug": "main_dishes"},
]

LOCATIONS = [
    {
        "name": "DaTeNO - District 1",
        "address": "123 Le Loi Street, Ben Thanh Ward, District 1, Ho Chi Minh City",
        "map_url": "https://maps.app.goo.gl/District1Branch",
    },
    {
        "name": "DaTeNO - District 7",
        "address": "456 Nguyen Van Linh Street, Tan Phong Ward, District 7, Ho Chi Minh City",
        "map_url": "https://maps.app.goo.gl/District7Branch",
    },
    {
        "name": "DaTeNO - Thu Duc",
        "address": "789 Vo Van Ngan Street, Linh Chieu Ward, Thu Duc City, Ho Chi Minh City",
        "map_url": "https://maps.app.goo.gl/ThuDucBranch",
    },
]

PRODUCTS = [
    {
        "category": "starters",
        "image_url": "starters/caesar_salad.webp",
        "name": "Classic Caesar Salad",
        "description": "Crisp romaine lettuce tossed in house-made creamy Caesar dressing. Topped with buttery croutons, aged Parmesan, and black pepper. A refreshing light start.",
        "price": "12.50",
        "slug": "caesar-salad",
    },
    {
        "category": "starters",
        "image_url": "starters/crab_corn_chicken_soup.webp",
        "name": "Crab, Corn & Chicken Soup",
        "description": "Thick Asian-style soup with fresh crab meat, sweet corn, and tender chicken. Simmered in rich broth and finished with a hint of sesame oil for a warm palate.",
        "price": "10.00",
        "slug": "crab-corn-chicken-soup",
    },
    {
        "category": "starters",
        "image_url": "starters/fish_sauce_chicken_wings.webp",
        "name": "Fish Sauce Chicken Wings",
        "description": "Golden fried chicken wings glazed in a savory and sweet garlic-infused fish sauce reduction. A perfect balance of salty and tangy flavors with a crispy finish.",
        "price": "14.50",
        "slug": "fish-sauce-chicken-wings",
    },
    {
        "category": "starters",
        "image_url": "starters/french_onion_soup.webp",
        "name": "French Onion Soup",
        "description": "Rich, slow-simmered onion broth topped with toasted artisan baguette and a thick layer of melted, bubbly Gruyere cheese. A classic Parisian comfort dish.",
        "price": "11.00",
        "slug": "french-onion-soup",
    },
    {
        "category": "starters",
        "image_url": "starters/garlic_butter_bread.webp",
        "name": "Garlic Butter Bread",
        "description": "Artisan baguette slices toasted with house-blended garlic butter made from premium butter, roasted garlic, and fresh parsley. Irresistibly crunchy and savory.",
        "price": "6.00",
        "slug": "garlic-butter-bread",
    },
    {
        "category": "starters",
        "image_url": "starters/herb_potato_wedges.webp",
        "name": "Herb Potato Wedges",
        "description": "Thick-cut potato wedges roasted with Mediterranean herbs like rosemary and thyme. Crispy on the outside and fluffy inside. Served with spicy garlic mayo.",
        "price": "8.50",
        "slug": "herb-potato-wedges",
    },
    {
        "category": "starters",
        "image_url": "starters/nha_trang_grilled_pork.webp",
        "name": "Nha Trang Grilled Pork",
        "description": "Skewers of lean pork marinated in lemongrass and local spices, grilled over charcoal for a smoky aroma. Served with traditional peanut dipping sauce.",
        "price": "15.00",
        "slug": "nha-trang-grilled-pork",
    },
    {
        "category": "starters",
        "image_url": "starters/papaya_salad_dried_beef.webp",
        "name": "Papaya Salad with Dried Beef",
        "description": "Crunchy green papaya and aromatic herbs tossed in zesty lime vinaigrette. Topped with savory dried beef and roasted peanuts for an explosion of textures.",
        "price": "13.00",
        "slug": "papaya-salad-dried-beef",
    },
    {
        "category": "starters",
        "image_url": "starters/seafood_spring_rolls_mayo.webp",
        "name": "Seafood Spring Rolls with Mayo",
        "description": "Crispy spring rolls stuffed with premium shrimp, squid, and taro. Served with a smooth, tangy Japanese mayonnaise dipping sauce for a rich seafood experience.",
        "price": "12.00",
        "slug": "seafood-spring-rolls-mayo",
    },
    {
        "category": "starters",
        "image_url": "starters/seaweed_flying_fish_roe_salad.webp",
        "name": "Seaweed & Roe Salad",
        "description": "Nutrient-rich chilled seaweed marinated in sesame oil and vinegar. Topped with crunchy flying fish roe that pops with every bite. Fresh and nutty flavor.",
        "price": "14.00",
        "slug": "seaweed-roe-salad",
    },
    {
        "category": "starters",
        "image_url": "starters/shrimp_pork_spring_rolls.webp",
        "name": "Shrimp & Pork Spring Rolls",
        "description": "Fresh rice paper rolls with poached tiger prawns, pork belly, vermicelli, and fresh mint. Served with a rich hoisin-peanut dipping sauce. Light and healthy.",
        "price": "9.50",
        "slug": "shrimp-pork-spring-rolls",
    },
    {
        "category": "starters",
        "image_url": "starters/silken_tofu_pork_floss_salted_egg.webp",
        "name": "Silken Tofu with Salted Egg",
        "description": "Velvety smooth silken tofu topped with rich salted egg yolk sauce, premium pork floss, and scallion oil. A unique contrast of cool tofu and savory toppings.",
        "price": "10.50",
        "slug": "silken-tofu-salted-egg",
    },
    {
        "category": "main_dishes",
        "image_url": "main_dishes/bbq_grilled_pork_ribs.webp",
        "name": "BBQ Grilled Pork Ribs",
        "description": "Fall-off-the-bone tender baby back ribs glazed in smoky hickory BBQ sauce. Grilled over an open flame and served with creamy coleslaw and buttered corn.",
        "price": "28.00",
        "slug": "bbq-grilled-pork-ribs",
    },
    {
        "category": "main_dishes",
        "image_url": "main_dishes/beef_steak_red_wine.webp",
        "name": "Beef Steak in Red Wine",
        "description": "Premium center-cut beef tenderloin seared to perfection and drizzled with a luxurious Cabernet Sauvignon reduction. Served with garlic mashed potatoes.",
        "price": "35.00",
        "slug": "beef-steak-red-wine",
    },
    {
        "category": "main_dishes",
        "image_url": "main_dishes/chicken_breast_rolled_with_mushrooms_in_cream_sauce.webp",
        "name": "Mushroom Cream Chicken Roll",
        "description": "Chicken breast rolled with sautéed wild mushrooms and herbs, oven-baked and smothered in a velvety Chardonnay cream sauce. Served with roasted vegetables.",
        "price": "24.50",
        "slug": "mushroom-cream-chicken",
    },
    {
        "category": "main_dishes",
        "image_url": "main_dishes/crispy_fried_noodles_with_seafood.webp",
        "name": "Crispy Seafood Fried Noodles",
        "description": "Bird’s nest crispy egg noodles topped with stir-fried tiger prawns, squid, and seasonal vegetables in a savory ginger-soy gravy. A delightful mix of textures.",
        "price": "18.00",
        "slug": "crispy-seafood-noodles",
    },
    {
        "category": "main_dishes",
        "image_url": "main_dishes/crispy_fried_stuffed_squid.webp",
        "name": "Crispy Stuffed Squid",
        "description": "Large fresh squid stuffed with seasoned minced pork and wood-ear mushrooms, fried until golden. Served with sweet chili sauce and fresh cucumbers.",
        "price": "22.00",
        "slug": "crispy-stuffed-squid",
    },
    {
        "category": "main_dishes",
        "image_url": "main_dishes/german_braised_pork_knuckle.webp",
        "name": "German Braised Pork Knuckle",
        "description": "Authentic Bavarian pork knuckle braised in dark beer and roasted until skin is crackling crisp. Served with sauerkraut, potato dumplings, and rich gravy.",
        "price": "32.00",
        "slug": "german-pork-knuckle",
    },
    {
        "category": "main_dishes",
        "image_url": "main_dishes/grilled_chicken_with_wild_honey.webp",
        "name": "Wild Honey Grilled Chicken",
        "description": "Half chicken marinated in wild mountain honey and garden herbs, grilled slowly for caramelized skin and juicy meat. Served with jasmine rice and ginger sauce.",
        "price": "20.00",
        "slug": "wild-honey-grilled-chicken",
    },
    {
        "category": "main_dishes",
        "image_url": "main_dishes/herb_grilled_lamb.webp",
        "name": "Herb Grilled Lamb Chops",
        "description": "Premium lamb chops marinated in rosemary and extra virgin olive oil. Char-broiled and served with mint jelly, roasted root vegetables, and red wine jus.",
        "price": "38.00",
        "slug": "herb-grilled-lamb",
    },
    {
        "category": "main_dishes",
        "image_url": "main_dishes/hong_kong_style_steamed_sea_bass.webp",
        "name": "HK Style Steamed Sea Bass",
        "description": "Fresh sea bass steamed with julienned ginger and scallions. Finished with sizzling premium soy sauce and hot peanut oil to release aromatic flavors.",
        "price": "30.00",
        "slug": "hk-steamed-sea-bass",
    },
    {
        "category": "main_dishes",
        "image_url": "main_dishes/pan_seared_salmon_with_passion_fruit_sauce.webp",
        "name": "Passion Fruit Salmon",
        "description": "Pan-seared Atlantic salmon fillet with crispy skin and flaky center. Balanced by a bright passion fruit reduction. Served on baby spinach and quinoa.",
        "price": "29.50",
        "slug": "passion-fruit-salmon",
    },
    {
        "category": "main_dishes",
        "image_url": "main_dishes/peking_roast_duck.webp",
        "name": "Peking Roast Duck",
        "description": "World-famous delicacy with thin, honey-glazed crispy skin. Served with warm handmade pancakes, scallions, cucumbers, and sweet hoisin dipping sauce.",
        "price": "45.00",
        "slug": "peking-roast-duck",
    },
    {
        "category": "main_dishes",
        "image_url": "main_dishes/royal_seafood_fried_rice.webp",
        "name": "Royal Seafood Fried Rice",
        "description": "Fragrant jasmine rice stir-fried with shrimp, squid, and scallops. Infused with natural golden turmeric and topped with crispy shallots and scallions.",
        "price": "16.50",
        "slug": "royal-seafood-fried-rice",
    },
    {
        "category": "main_dishes",
        "image_url": "main_dishes/seafood_cheese_pizza.webp",
        "name": "Seafood Cheese Pizza",
        "description": "Stone-baked thin crust pizza topped with San Marzano tomato sauce, Mozzarella, tiger prawns, and squid rings. Finished with dried oregano and chili flakes.",
        "price": "19.00",
        "slug": "seafood-cheese-pizza",
    },
    {
        "category": "main_dishes",
        "image_url": "main_dishes/shaking_beef_with_french_fries.webp",
        "name": "Shaking Beef with Fries",
        "description": "Premium beef tenderloin cubes wok-tossed with red onions and a savory soy-butter glaze. Served with fresh salad and crispy golden-brown French fries.",
        "price": "26.00",
        "slug": "shaking-beef-fries",
    },
    {
        "category": "main_dishes",
        "image_url": "main_dishes/spaghetti_bolognese.webp",
        "name": "Classic Spaghetti Bolognese",
        "description": "Al dente spaghetti smothered in a deep, rich meat sauce slow-simmered for eight hours with premium beef and vine-ripened tomatoes. Topped with parmesan.",
        "price": "15.50",
        "slug": "spaghetti-bolognese",
    },
    {
        "category": "main_dishes",
        "image_url": "main_dishes/steamed_giant_prawns_with_coconut_water.webp",
        "name": "Coconut Steamed Prawns",
        "description": "Jumbo tiger prawns steamed inside a fresh young coconut to infuse natural sweetness. Served with a zesty green chili and lime dipping sauce.",
        "price": "25.00",
        "slug": "coconut-steamed-prawns",
    },
    {
        "category": "main_dishes",
        "image_url": "main_dishes/thai_green_chicken_curry.webp",
        "name": "Thai Green Chicken Curry",
        "description": "Aromatic and spicy classic curry with tender chicken, coconut milk, lemongrass, and Thai basil. Best enjoyed with fragrant jasmine rice.",
        "price": "18.50",
        "slug": "thai-green-curry",
    },
    {
        "category": "main_dishes",
        "image_url": "main_dishes/thai_spicy_and_sour_seafood_hot_pot.webp",
        "name": "Thai Spicy Seafood Hot Pot",
        "description": "Grand pot of spicy Tom Yum broth packed with tiger prawns, squid, and fish. A perfect balance of spicy, sour, and savory flavors designed for sharing.",
        "price": "42.00",
        "slug": "thai-seafood-hotpot",
    },
]

categories = sa.table(
    "categories", sa.column("id", sa.Integer), sa.column("name"), sa.column("slug")
)
locations = sa.table(
    "locations",
    sa.column("id", sa.Integer),
    sa.column("name"),
    sa.column("address"),
    sa.column("map_url"),
)
products = sa.table(
    "products",
    sa.column("id", sa.Integer),
    sa.column("category_id", sa.Integer),
    sa.column("image_url"),
    sa.column("name"),
    sa.column("description"),
    sa.column("price", sa.Numeric(10, 2)),
    sa.column("slug"),
)
product_availabilities = sa.table(
    "product_availabilities",
    sa.column("product_id", sa.Integer),
    sa.column("location_id", sa.Integer),
)


def upgrade() -> None:
    # IDs are looked up instead of hard-coded so Postgres sequences stay in sync.
    op.bulk_insert(categories, CATEGORIES)
    op.bulk_insert(locations, LOCATIONS)

    conn = op.get_bind()
    category_ids = dict(conn.execute(sa.select(categories.c.slug, categories.c.id)).all())
    op.bulk_insert(
        products,
        [
            {
                **{k: v for k, v in p.items() if k != "category"},
                "category_id": category_ids[p["category"]],
            }
            for p in PRODUCTS
        ],
    )

    product_ids = conn.execute(sa.select(products.c.id)).scalars().all()
    location_ids = conn.execute(sa.select(locations.c.id)).scalars().all()
    op.bulk_insert(
        product_availabilities,
        [{"product_id": p, "location_id": loc} for p in product_ids for loc in location_ids],
    )


def downgrade() -> None:
    op.execute(product_availabilities.delete())
    op.execute(products.delete().where(products.c.slug.in_([p["slug"] for p in PRODUCTS])))
    op.execute(locations.delete().where(locations.c.name.in_([loc["name"] for loc in LOCATIONS])))
    op.execute(categories.delete().where(categories.c.slug.in_([c["slug"] for c in CATEGORIES])))
