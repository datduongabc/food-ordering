"""bilingual catalog content

Revision ID: 7d3a9c2e5f18
Revises: 5c2d8f1a7b34
Create Date: 2026-10-29 07:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7d3a9c2e5f18"
down_revision: str | Sequence[str] | None = "5c2d8f1a7b34"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CATEGORIES_VI = {"starters": "Khai vị", "main_dishes": "Món chính"}

# Keyed by the English branch name the seed migration inserted.
LOCATIONS_VI = {
    "DaTeNO - District 1": (
        "DaTeNO - Quận 1",
        "123 Lê Lợi, Phường Bến Thành, Quận 1, TP. Hồ Chí Minh",
    ),
    "DaTeNO - District 7": (
        "DaTeNO - Quận 7",
        "456 Nguyễn Văn Linh, Phường Tân Phong, Quận 7, TP. Hồ Chí Minh",
    ),
    "DaTeNO - Thu Duc": (
        "DaTeNO - Thủ Đức",
        "789 Võ Văn Ngân, Phường Linh Chiểu, TP. Thủ Đức, TP. Hồ Chí Minh",
    ),
}

# Keyed by slug, which the seed migration fixed for every dish.
PRODUCTS_VI = {
    "caesar-salad": (
        "Salad Caesar truyền thống",
        "Xà lách romaine giòn trộn sốt Caesar nhà làm, thêm bánh mì nướng bơ, phô mai Parmesan và tiêu đen. Món khai vị nhẹ nhàng, thanh mát.",
    ),
    "crab-corn-chicken-soup": (
        "Súp cua bắp gà",
        "Súp sánh kiểu Á với thịt cua tươi, bắp ngọt và thịt gà mềm, nấu trong nước dùng đậm đà và thơm nhẹ dầu mè.",
    ),
    "fish-sauce-chicken-wings": (
        "Cánh gà chiên nước mắm",
        "Cánh gà chiên vàng giòn, áo lớp nước mắm tỏi sánh mặn ngọt hài hòa.",
    ),
    "french-onion-soup": (
        "Súp hành kiểu Pháp",
        "Nước dùng hành tây ninh chậm, phủ bánh mì baguette nướng và lớp phô mai Gruyère tan chảy. Món ăn ấm lòng kiểu Paris.",
    ),
    "garlic-butter-bread": (
        "Bánh mì bơ tỏi",
        "Bánh mì baguette nướng giòn với bơ tỏi nhà làm từ bơ thượng hạng, tỏi nướng và ngò tây tươi.",
    ),
    "herb-potato-wedges": (
        "Khoai tây múi cau nướng thảo mộc",
        "Khoai tây cắt múi cau nướng với hương thảo và cỏ xạ hương, giòn ngoài mềm trong, dùng kèm sốt mayonnaise tỏi cay.",
    ),
    "nha-trang-grilled-pork": (
        "Nem nướng Nha Trang",
        "Thịt heo nạc ướp sả và gia vị, nướng than hồng thơm khói, dùng kèm nước chấm đậu phộng truyền thống.",
    ),
    "papaya-salad-dried-beef": (
        "Gỏi đu đủ khô bò",
        "Đu đủ xanh giòn và rau thơm trộn nước trộn chanh chua ngọt, thêm khô bò đậm vị và đậu phộng rang.",
    ),
    "seafood-spring-rolls-mayo": (
        "Chả giò hải sản sốt mayonnaise",
        "Chả giò chiên giòn nhân tôm, mực và khoai môn, dùng kèm sốt mayonnaise Nhật béo nhẹ.",
    ),
    "seaweed-roe-salad": (
        "Gỏi rong biển trứng cá",
        "Rong biển ướp lạnh với dầu mè và giấm, phủ trứng cá chuồn giòn tan. Vị tươi mát, thơm bùi.",
    ),
    "shrimp-pork-spring-rolls": (
        "Gỏi cuốn tôm thịt",
        "Bánh tráng cuốn tôm sú luộc, thịt ba chỉ, bún và rau thơm, dùng kèm tương đậu phộng béo bùi. Món khai vị thanh nhẹ.",
    ),
    "silken-tofu-salted-egg": (
        "Đậu hũ non sốt trứng muối",
        "Đậu hũ non mềm mịn phủ sốt trứng muối béo ngậy, chà bông và mỡ hành.",
    ),
    "bbq-grilled-pork-ribs": (
        "Sườn heo nướng BBQ",
        "Sườn non mềm rút xương, phết sốt BBQ khói, nướng lửa trực tiếp, dùng kèm salad bắp cải và bắp nướng bơ.",
    ),
    "beef-steak-red-wine": (
        "Bò bít tết sốt vang đỏ",
        "Thăn bò thượng hạng áp chảo vừa tới, rưới sốt vang Cabernet Sauvignon, dùng kèm khoai tây nghiền tỏi.",
    ),
    "mushroom-cream-chicken": (
        "Gà cuộn nấm sốt kem",
        "Ức gà cuộn nấm rừng xào và thảo mộc, nướng lò rồi phủ sốt kem vang Chardonnay, dùng kèm rau củ nướng.",
    ),
    "crispy-seafood-noodles": (
        "Mì xào giòn hải sản",
        "Mì trứng chiên giòn hình tổ chim, phủ tôm sú, mực và rau củ xào sốt gừng xì dầu.",
    ),
    "crispy-stuffed-squid": (
        "Mực nhồi thịt chiên giòn",
        "Mực tươi nhồi thịt heo băm và nấm mèo, chiên vàng giòn, dùng kèm tương ớt ngọt và dưa leo.",
    ),
    "german-pork-knuckle": (
        "Giò heo hầm kiểu Đức",
        "Giò heo kiểu Bavaria hầm bia đen rồi quay da giòn rụm, dùng kèm dưa cải chua, bánh khoai tây và nước sốt đậm đà.",
    ),
    "wild-honey-grilled-chicken": (
        "Gà nướng mật ong rừng",
        "Nửa con gà ướp mật ong rừng và thảo mộc, nướng chậm cho da caramel và thịt mọng nước, dùng kèm cơm lài và nước chấm gừng.",
    ),
    "herb-grilled-lamb": (
        "Sườn cừu nướng thảo mộc",
        "Sườn cừu thượng hạng ướp hương thảo và dầu ô liu, nướng than, dùng kèm thạch bạc hà, rau củ nướng và sốt vang đỏ.",
    ),
    "hk-steamed-sea-bass": (
        "Cá chẽm hấp kiểu Hồng Kông",
        "Cá chẽm tươi hấp gừng hành, rưới xì dầu thượng hạng và dầu phộng nóng cho dậy mùi thơm.",
    ),
    "passion-fruit-salmon": (
        "Cá hồi sốt chanh dây",
        "Phi lê cá hồi áp chảo da giòn, sốt chanh dây chua ngọt, dùng kèm cải bó xôi non và hạt diêm mạch.",
    ),
    "peking-roast-duck": (
        "Vịt quay Bắc Kinh",
        "Vịt quay da mỏng giòn phết mật ong, cuốn bánh tráng mỏng cùng hành lá, dưa leo và tương hoisin.",
    ),
    "royal-seafood-fried-rice": (
        "Cơm chiên hải sản hoàng gia",
        "Cơm lài chiên với tôm, mực và sò điệp, thơm màu nghệ vàng, rắc hành phi giòn và hành lá.",
    ),
    "seafood-cheese-pizza": (
        "Pizza hải sản phô mai",
        "Pizza đế mỏng nướng lò đá với sốt cà chua San Marzano, phô mai Mozzarella, tôm sú và mực, rắc lá oregano và ớt khô.",
    ),
    "shaking-beef-fries": (
        "Bò lúc lắc khoai tây chiên",
        "Thăn bò cắt khối xào lửa lớn với hành tây và sốt bơ xì dầu, dùng kèm salad và khoai tây chiên vàng giòn.",
    ),
    "spaghetti-bolognese": (
        "Mì Ý sốt bò bằm",
        "Mì spaghetti chín tới với sốt thịt bò và cà chua ninh suốt tám giờ, rắc phô mai Parmesan.",
    ),
    "coconut-steamed-prawns": (
        "Tôm càng hấp nước dừa",
        "Tôm sú cỡ lớn hấp trong trái dừa xiêm tươi cho vị ngọt tự nhiên, dùng kèm muối ớt xanh chanh.",
    ),
    "thai-green-curry": (
        "Cà ri xanh gà kiểu Thái",
        "Cà ri cay thơm với thịt gà mềm, nước cốt dừa, sả và húng quế Thái. Ngon nhất khi ăn cùng cơm lài.",
    ),
    "thai-seafood-hotpot": (
        "Lẩu Thái hải sản",
        "Nồi lẩu Tom Yum chua cay đầy đủ tôm sú, mực và cá. Vị cay, chua, đậm đà hài hòa, phù hợp dùng chung.",
    ),
}


def _rename_and_add(table: str, pairs: list[tuple[str, sa.types.TypeEngine]]) -> None:
    with op.batch_alter_table(table) as batch_op:
        for column, type_ in pairs:
            batch_op.alter_column(column, new_column_name=f"{column}_en", existing_type=type_)
            batch_op.add_column(sa.Column(f"{column}_vi", type_, nullable=True))


def _require(table: str, pairs: list[tuple[str, sa.types.TypeEngine]]) -> None:
    with op.batch_alter_table(table) as batch_op:
        for column, type_ in pairs:
            batch_op.alter_column(f"{column}_vi", existing_type=type_, nullable=False)


CATEGORY_COLUMNS = [("name", sa.String(255))]
LOCATION_COLUMNS = [("name", sa.String(255)), ("address", sa.Text())]
PRODUCT_COLUMNS = [("name", sa.String(255)), ("description", sa.String(500))]


def upgrade() -> None:
    """Upgrade schema."""
    _rename_and_add("categories", CATEGORY_COLUMNS)
    _rename_and_add("locations", LOCATION_COLUMNS)
    _rename_and_add("products", PRODUCT_COLUMNS)

    bind = op.get_bind()
    categories = sa.table(
        "categories", sa.column("slug"), sa.column("name_en"), sa.column("name_vi")
    )
    locations = sa.table(
        "locations",
        sa.column("name_en"),
        sa.column("name_vi"),
        sa.column("address_en"),
        sa.column("address_vi"),
    )
    products = sa.table(
        "products",
        sa.column("slug"),
        sa.column("name_en"),
        sa.column("name_vi"),
        sa.column("description_en"),
        sa.column("description_vi"),
    )

    for slug, name in CATEGORIES_VI.items():
        bind.execute(categories.update().where(categories.c.slug == slug).values(name_vi=name))
    for name_en, (name, address) in LOCATIONS_VI.items():
        bind.execute(
            locations.update()
            .where(locations.c.name_en == name_en)
            .values(name_vi=name, address_vi=address)
        )
    for slug, (name, description) in PRODUCTS_VI.items():
        bind.execute(
            products.update()
            .where(products.c.slug == slug)
            .values(name_vi=name, description_vi=description)
        )

    # Rows added after the seed (e.g. by an admin) have no translation yet; start them from
    # the English text so the columns can be required, and let the admin edit them.
    bind.execute(
        categories.update()
        .where(categories.c.name_vi.is_(None))
        .values(name_vi=categories.c.name_en)
    )
    bind.execute(
        locations.update()
        .where(locations.c.name_vi.is_(None))
        .values(name_vi=locations.c.name_en, address_vi=locations.c.address_en)
    )
    bind.execute(
        products.update()
        .where(products.c.name_vi.is_(None))
        .values(name_vi=products.c.name_en, description_vi=products.c.description_en)
    )

    _require("categories", CATEGORY_COLUMNS)
    _require("locations", LOCATION_COLUMNS)
    _require("products", PRODUCT_COLUMNS)


def downgrade() -> None:
    """Downgrade schema."""
    for table, pairs in (
        ("products", PRODUCT_COLUMNS),
        ("locations", LOCATION_COLUMNS),
        ("categories", CATEGORY_COLUMNS),
    ):
        with op.batch_alter_table(table) as batch_op:
            for column, type_ in pairs:
                batch_op.drop_column(f"{column}_vi")
                batch_op.alter_column(f"{column}_en", new_column_name=column, existing_type=type_)
