"""desserts, drinks and more main dishes

Adds the Desserts and Drinks categories with ten items each, and ten Vietnamese main dishes.
Photos come from Wikimedia Commons; see media/products/CREDITS.md.

Revision ID: 5c2e8a91d7f3
Revises: 30b9ab2e6605
Create Date: 2026-10-30 04:00:00

"""

import unicodedata
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "5c2e8a91d7f3"
down_revision: str | Sequence[str] | None = "30b9ab2e6605"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CATEGORIES = [
    {"slug": "desserts", "name_vi": "Tráng miệng", "name_en": "Desserts"},
    {"slug": "drinks", "name_vi": "Đồ uống", "name_en": "Drinks"},
]

# (category, slug, image, name_vi, name_en, description_vi, description_en, price in VND)
PRODUCTS = [
    # --- Main dishes ---
    (
        "main_dishes",
        "wagyu-beef-pho",
        "main_dishes/wagyu_beef_pho.webp",
        "Phở bò Wagyu",
        "Wagyu Beef Pho",
        "Nước dùng xương bò hầm 12 tiếng với quế, hồi và thảo quả, dọn cùng bánh phở tươi và "
        "thịt bò Wagyu thái mỏng chần tái. Ăn kèm rau thơm, giá, chanh và ớt.",
        "Beef bone broth simmered for 12 hours with cinnamon, star anise and black cardamom, "
        "poured over fresh rice noodles and thinly sliced Wagyu beef. Served with herbs, bean "
        "sprouts, lime and chilli.",
        395_000,
    ),
    (
        "main_dishes",
        "hanoi-bun-cha",
        "main_dishes/hanoi_bun_cha.webp",
        "Bún chả Hà Nội",
        "Hanoi Bun Cha",
        "Chả viên và thịt ba chỉ nướng than hoa ngâm trong nước mắm chua ngọt, ăn cùng bún "
        "tươi, rau sống và tỏi ớt ngâm.",
        "Charcoal-grilled pork patties and pork belly in a sweet and tangy fish sauce, with "
        "fresh rice vermicelli, herbs and pickled garlic and chilli.",
        345_000,
    ),
    (
        "main_dishes",
        "broken-rice-pork-chop",
        "main_dishes/broken_rice_pork_chop.webp",
        "Cơm tấm sườn nướng",
        "Broken Rice with Grilled Pork Chop",
        "Sườn cốt lết ướp sả và mật ong nướng than, dọn cùng cơm tấm, mỡ hành, đồ chua và "
        "nước mắm pha.",
        "Lemongrass and honey marinated pork chop grilled over charcoal, with broken rice, "
        "scallion oil, pickles and sweet fish sauce.",
        335_000,
    ),
    (
        "main_dishes",
        "caramelized-fish-clay-pot",
        "main_dishes/caramelized_fish_clay_pot.webp",
        "Cá kho tộ",
        "Caramelised Fish in Clay Pot",
        "Khúc cá kho trong niêu đất với nước màu, nước mắm và tiêu đen đến khi sánh lại. Dọn "
        "kèm cơm trắng nóng.",
        "Fish steaks braised in a clay pot with caramel, fish sauce and cracked black pepper "
        "until sticky and glossy. Served with steamed jasmine rice.",
        425_000,
    ),
    (
        "main_dishes",
        "vietnamese-beef-stew",
        "main_dishes/vietnamese_beef_stew.webp",
        "Bò kho bánh mì",
        "Vietnamese Beef Stew with Baguette",
        "Bắp bò hầm mềm với sả, hoa hồi và cà rốt trong nước sốt cà chua đậm vị, ăn kèm bánh mì "
        "nướng giòn.",
        "Beef shank slow-braised with lemongrass, star anise and carrots in a rich tomato "
        "gravy, served with a crusty toasted baguette.",
        385_000,
    ),
    (
        "main_dishes",
        "tamarind-crab",
        "main_dishes/tamarind_crab.webp",
        "Cua rang me",
        "Tamarind Mud Crab",
        "Cua bùn Cà Mau rang với sốt me chua ngọt, tỏi phi và rau răm. Phần dành cho 2 người.",
        "Ca Mau mud crab wok-tossed in sweet and sour tamarind sauce with fried garlic and "
        "Vietnamese coriander. Serves two.",
        1_150_000,
    ),
    (
        "main_dishes",
        "black-pepper-crab",
        "main_dishes/black_pepper_crab.webp",
        "Cua sốt tiêu đen",
        "Black Pepper Crab",
        "Cua bùn xào lửa lớn với tiêu đen Phú Quốc xay thô, bơ và hành tây, thơm nồng và cay "
        "ấm. Phần dành cho 2 người.",
        "Mud crab stir-fried over high heat with coarse Phu Quoc black pepper, butter and "
        "onions, fragrant and warmly spicy. Serves two.",
        1_150_000,
    ),
    (
        "main_dishes",
        "hue-spicy-beef-noodles",
        "main_dishes/hue_spicy_beef_noodles.webp",
        "Bún bò Huế",
        "Hue Spicy Beef Noodle Soup",
        "Nước dùng xương bò thơm sả và mắm ruốc, sợi bún to, bắp bò, giò heo và chả cua. Thêm "
        "sa tế cay theo khẩu vị.",
        "Beef broth scented with lemongrass and shrimp paste, with thick rice noodles, beef "
        "shank, pork knuckle and crab cake. Add house chilli oil to taste.",
        365_000,
    ),
    (
        "main_dishes",
        "grilled-snakehead-fish",
        "main_dishes/grilled_snakehead_fish.webp",
        "Cá lóc nướng trui",
        "Straw-Grilled Snakehead Fish",
        "Cá lóc đồng nướng nguyên con theo kiểu miền Tây, cuốn bánh tráng với rau rừng và bún, "
        "chấm mắm me. Phần dành cho 2 người.",
        "A whole snakehead fish grilled Mekong Delta style, to wrap in rice paper with wild "
        "greens and vermicelli and dip in tamarind fish sauce. Serves two.",
        560_000,
    ),
    (
        "main_dishes",
        "hoi-an-chicken-rice",
        "main_dishes/hoi_an_chicken_rice.webp",
        "Cơm gà Hội An",
        "Hoi An Chicken Rice",
        "Cơm nấu nước luộc gà và nghệ vàng óng, ăn cùng gà ta xé phay trộn rau răm, hành tây và "
        "tương ớt Hội An.",
        "Rice cooked golden in chicken stock and turmeric, topped with shredded free-range "
        "chicken tossed with Vietnamese coriander and onion, with Hoi An chilli sauce.",
        325_000,
    ),
    # --- Desserts ---
    (
        "desserts",
        "three-colour-sweet-soup",
        "desserts/three_colour_sweet_soup.webp",
        "Chè ba màu",
        "Three-Colour Sweet Soup",
        "Đậu đỏ, đậu xanh đánh và thạch lá dứa xếp lớp, rưới nước cốt dừa béo và đá bào.",
        "Layers of red beans, mung bean paste and pandan jelly, topped with rich coconut "
        "cream and shaved ice.",
        85_000,
    ),
    (
        "desserts",
        "caramel-flan",
        "desserts/caramel_flan.webp",
        "Bánh flan caramel",
        "Caramel Flan",
        "Bánh flan trứng gà và sữa tươi hấp mềm mịn, phủ lớp caramel đắng nhẹ.",
        "Silky steamed custard of eggs and fresh milk under a lightly bitter caramel.",
        75_000,
    ),
    (
        "desserts",
        "almond-jelly-lychee",
        "desserts/almond_jelly_lychee.webp",
        "Chè khúc bạch vải",
        "Almond Jelly with Lychee",
        "Khúc bạch hạnh nhân và phô mai cắt viên, dọn cùng vải thiều, hạnh nhân lát và nước "
        "đường hoa nhài mát lạnh.",
        "Cubes of almond and cream cheese jelly with lychees, toasted almond flakes and "
        "chilled jasmine syrup.",
        95_000,
    ),
    (
        "desserts",
        "black-sticky-rice-yogurt",
        "desserts/black_sticky_rice_yogurt.webp",
        "Sữa chua nếp cẩm",
        "Black Sticky Rice Yogurt",
        "Sữa chua nhà làm sánh mịn trên lớp nếp cẩm dẻo thơm ủ nhẹ, vị chua ngọt hài hòa.",
        "Creamy house-made yogurt over chewy, gently fermented black sticky rice, sweet and tangy.",
        79_000,
    ),
    (
        "desserts",
        "coconut-mixed-sweet-soup",
        "desserts/coconut_mixed_sweet_soup.webp",
        "Chè thập cẩm nước cốt dừa",
        "Mixed Sweet Soup with Coconut Cream",
        "Khoai môn, mít, thạch lá dứa và trân châu trong nước cốt dừa thơm béo, dùng nóng hoặc "
        "lạnh.",
        "Taro, jackfruit, pandan jelly and tapioca pearls in fragrant coconut cream, served "
        "warm or chilled.",
        89_000,
    ),
    (
        "desserts",
        "baked-banana-cake",
        "desserts/baked_banana_cake.webp",
        "Bánh chuối nướng",
        "Baked Banana Cake",
        "Chuối sứ chín, bánh mì và nước cốt dừa nướng đến vàng thơm, rắc đậu phộng rang.",
        "Ripe Vietnamese bananas baked with bread and coconut milk until golden, sprinkled "
        "with roasted peanuts.",
        85_000,
    ),
    (
        "desserts",
        "vietnamese-coffee-tiramisu",
        "desserts/vietnamese_coffee_tiramisu.webp",
        "Tiramisu cà phê phin",
        "Vietnamese Coffee Tiramisu",
        "Bánh ladyfinger thấm cà phê phin Buôn Ma Thuột, xen lớp kem mascarpone và phủ bột cacao.",
        "Ladyfingers soaked in Buon Ma Thuot drip coffee, layered with mascarpone cream and "
        "dusted with cocoa.",
        145_000,
    ),
    (
        "desserts",
        "coconut-ice-cream",
        "desserts/coconut_ice_cream.webp",
        "Kem dừa",
        "Coconut Ice Cream",
        "Kem dừa nhà làm dọn trong gáo dừa, kèm cơm dừa non và thạch đỏ dẻo.",
        "House-made coconut ice cream served in a coconut shell with young coconut flesh and "
        "chewy red jellies.",
        115_000,
    ),
    (
        "desserts",
        "passion-fruit-panna-cotta",
        "desserts/passion_fruit_panna_cotta.webp",
        "Panna cotta chanh dây",
        "Passion Fruit Panna Cotta",
        "Panna cotta kem vani mềm mịn, rưới sốt chanh dây Đà Lạt chua thanh.",
        "Silky vanilla panna cotta with a bright, tangy Da Lat passion fruit sauce.",
        115_000,
    ),
    (
        "desserts",
        "ginger-rice-balls",
        "desserts/ginger_rice_balls.webp",
        "Chè trôi nước gừng",
        "Glutinous Rice Balls in Ginger Syrup",
        "Viên nếp dẻo nhân đậu xanh trong nước đường gừng ấm, rắc mè rang và nước cốt dừa.",
        "Chewy glutinous rice balls filled with mung bean in warm ginger syrup, topped with "
        "toasted sesame and coconut cream.",
        79_000,
    ),
    # --- Drinks ---
    (
        "drinks",
        "iced-milk-coffee",
        "drinks/iced_milk_coffee.webp",
        "Cà phê sữa đá",
        "Vietnamese Iced Milk Coffee",
        "Cà phê Robusta pha phin đậm đặc, hòa cùng sữa đặc và đá.",
        "Strong Robusta coffee from a phin filter, stirred with condensed milk over ice.",
        55_000,
    ),
    (
        "drinks",
        "salted-cream-coffee",
        "drinks/salted_cream_coffee.webp",
        "Cà phê muối",
        "Salted Cream Coffee",
        "Cà phê phin phủ lớp kem sữa đánh với chút muối biển, vị mặn nhẹ làm nổi bật vị đắng ngọt.",
        "Drip coffee crowned with whipped cream and a pinch of sea salt, which brings out its "
        "bittersweet notes.",
        65_000,
    ),
    (
        "drinks",
        "bac-xiu",
        "drinks/bac_xiu.webp",
        "Bạc xỉu",
        "Bac Xiu White Coffee",
        "Nhiều sữa, ít cà phê: sữa tươi và sữa đặc với một chút cà phê phin, ngọt béo và dịu nhẹ.",
        "Mostly milk, a little coffee: fresh and condensed milk with a dash of drip coffee, "
        "sweet, creamy and mellow.",
        59_000,
    ),
    (
        "drinks",
        "egg-coffee",
        "drinks/egg_coffee.webp",
        "Cà phê trứng",
        "Hanoi Egg Coffee",
        "Lòng đỏ trứng đánh bông cùng sữa đặc thành lớp kem mịn, đặt trên cà phê nóng theo kiểu "
        "Hà Nội.",
        "Egg yolk whipped with condensed milk into a velvety cream, set on hot coffee the "
        "Hanoi way.",
        75_000,
    ),
    (
        "drinks",
        "peach-lemongrass-tea",
        "drinks/peach_lemongrass_tea.webp",
        "Trà đào cam sả",
        "Peach, Orange & Lemongrass Tea",
        "Trà đen ủ lạnh với đào ngâm, cam vắt và sả đập dập, thơm mát và ít ngọt.",
        "Cold-steeped black tea with peaches, fresh orange and bruised lemongrass, fragrant "
        "and lightly sweet.",
        69_000,
    ),
    (
        "drinks",
        "lotus-tea",
        "drinks/lotus_tea.webp",
        "Trà sen",
        "Lotus Tea",
        "Trà xanh Thái Nguyên ướp hương sen Tây Hồ, pha nóng trong ấm và dùng cùng mứt gừng.",
        "Thai Nguyen green tea scented with West Lake lotus, brewed hot in a pot and served "
        "with candied ginger.",
        85_000,
    ),
    (
        "drinks",
        "sugarcane-kumquat-juice",
        "drinks/sugarcane_kumquat_juice.webp",
        "Nước mía tắc",
        "Sugarcane Juice with Kumquat",
        "Mía ép tươi mỗi ngày, thêm tắc cho vị chua nhẹ, uống với đá.",
        "Sugarcane pressed fresh every day with a squeeze of kumquat, served over ice.",
        45_000,
    ),
    (
        "drinks",
        "avocado-smoothie",
        "drinks/avocado_smoothie.webp",
        "Sinh tố bơ",
        "Avocado Smoothie",
        "Bơ sáp Đắk Lắk xay mịn cùng sữa tươi và sữa đặc, sánh béo như kem.",
        "Buttery Dak Lak avocado blended with fresh and condensed milk until thick and creamy.",
        79_000,
    ),
    (
        "drinks",
        "fresh-coconut",
        "drinks/fresh_coconut.webp",
        "Dừa tươi",
        "Fresh Young Coconut",
        "Dừa xiêm Bến Tre ướp lạnh: uống nước dừa rồi ăn phần cơm dừa non.",
        "A chilled young Ben Tre coconut: drink the water, then scoop out the soft flesh.",
        59_000,
    ),
    (
        "drinks",
        "pennywort-juice",
        "drinks/pennywort_juice.webp",
        "Rau má đậu xanh",
        "Pennywort & Mung Bean Juice",
        "Rau má tươi xay cùng đậu xanh và nước cốt dừa, thanh mát và giải nhiệt.",
        "Fresh pennywort blended with mung beans and coconut milk, cool and refreshing.",
        55_000,
    ),
]

categories = sa.table(
    "categories",
    sa.column("id", sa.Integer),
    sa.column("slug"),
    sa.column("name_vi"),
    sa.column("name_en"),
)
products = sa.table(
    "products",
    sa.column("id", sa.Integer),
    sa.column("category_id", sa.Integer),
    sa.column("image_url"),
    sa.column("name_vi"),
    sa.column("name_en"),
    sa.column("description_vi"),
    sa.column("description_en"),
    sa.column("price", sa.BigInteger),
    sa.column("slug"),
    sa.column("search_text"),
)
locations = sa.table("locations", sa.column("id", sa.Integer))
product_availabilities = sa.table(
    "product_availabilities",
    sa.column("product_id", sa.Integer),
    sa.column("location_id", sa.Integer),
)


def fold(text: str) -> str:
    # A frozen copy of app.core.text.fold; bulk inserts skip the ORM event that fills it.
    decomposed = unicodedata.normalize("NFD", text.replace("đ", "d").replace("Đ", "D"))
    bare = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(bare.casefold().split())


def upgrade() -> None:
    op.bulk_insert(categories, CATEGORIES)

    conn = op.get_bind()
    category_ids = dict(conn.execute(sa.select(categories.c.slug, categories.c.id)).all())
    op.bulk_insert(
        products,
        [
            {
                "category_id": category_ids[category],
                "slug": slug,
                "image_url": image,
                "name_vi": name_vi,
                "name_en": name_en,
                "description_vi": description_vi,
                "description_en": description_en,
                "price": price,
                "search_text": fold(f"{name_vi} {name_en}"),
            }
            for category, slug, image, name_vi, name_en, description_vi, description_en, price in (
                PRODUCTS
            )
        ],
    )

    # Every branch serves the new dishes, like the original menu.
    new_ids = (
        conn.execute(sa.select(products.c.id).where(products.c.slug.in_([p[1] for p in PRODUCTS])))
        .scalars()
        .all()
    )
    location_ids = conn.execute(sa.select(locations.c.id)).scalars().all()
    op.bulk_insert(
        product_availabilities,
        [{"product_id": p, "location_id": loc} for p in new_ids for loc in location_ids],
    )


def downgrade() -> None:
    slugs = [p[1] for p in PRODUCTS]
    new_ids = sa.select(products.c.id).where(products.c.slug.in_(slugs)).scalar_subquery()
    op.execute(
        product_availabilities.delete().where(product_availabilities.c.product_id.in_(new_ids))
    )
    op.execute(products.delete().where(products.c.slug.in_(slugs)))
    op.execute(categories.delete().where(categories.c.slug.in_([c["slug"] for c in CATEGORIES])))
