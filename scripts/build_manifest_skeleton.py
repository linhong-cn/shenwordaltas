#!/usr/bin/env python3
"""
Build output/fix-plan/manifest_skeleton.json from scratch/audit_raw.json and
the audited P2 mismatch + ref_keep lists.
"""
import json, re
from pathlib import Path

SCRATCH = Path("/Users/hong/.gemini/antigravity/brain/83c705c9-c701-4e5c-82b5-5ceda4eabcb4/scratch")
OUT_DIR = Path("/Users/hong/WorkBuddy/shenwordaltas/output/fix-plan")
OUT_DIR.mkdir(parents=True, exist_ok=True)

raw = json.loads((SCRATCH / "audit_raw.json").read_text(encoding="utf-8"))

# 62 ref items confirmed safe to keep as-is
REF_KEEP = {
    # 13 exact morphological/article variants
    "activities", "grandparents", "parents", "shoes", "feelings", "needs", "wants",
    "the internet", "the moon", "the deaf", "relaxed", "bored", "luck",
    # 49 exact-scene phrase matches
    "play football", "play basketball", "play volleyball", "play beach volleyball",
    "play badminton", "play the piano", "play the violin", "play the guitar",
    "look at", "watch a film", "fly a kite", "kite-flying", "cross the road",
    "a lot of", "lots of", "want to do", "play a game", "take a photo", "take photos",
    "tell a story", "storyteller", "a pair of", "go home", "how many",
    "a bar of chocolate", "go shopping", "do exercise", "do housework", "do gardening",
    "have breakfast", "go to school", "have lunch", "police officer", "bus driver",
    "musical instrument", "by mistake", "sea turtle", "chat with", "water the flowers",
    "be busy with", "send an email", "go hiking", "go ice skating", "i'm so excited!",
    "be famous for", "art gallery", "take a trip", "pay attention to", "beg your pardon",
}

# P2 single-word polysemy mismatches: list of (slug_suffix, word_key, zh_filter_list, reason)
# If a word has TWO distinct mismatched senses (e.g. light: 灯 vs 轻的; miss: 小姐 vs 想念; pick: 捡起 vs 采；摘),
# we split them into separate image items so each gets an accurate illustration!
P2_SPECS = [
    ("rubber", "rubber", ["橡皮"], "教材指橡皮(eraser)，原图为橡胶靴"),
    ("paint", "paint", ["绘画", "用颜料画"], "教材指绘画动作，原图为手沾蓝色颜料"),
    ("fat", "fat", ["胖的", "肥的；胖的"], "教材指胖的，原图为撇去汤上油脂"),
    ("thin_slim", "thin", ["瘦的"], "G1指瘦的，原图为薄外套"),
    ("short_height", "short", ["矮的"], "G1/G2指矮的，原图为短散步"),
    ("orange_color", "orange", ["橘黄色；橘黄色的"], "G3指橘黄色，原图为剥橙子"),
    ("bear", "bear", ["熊"], "教材指动物熊，原图为忍受噪声"),
    ("chicken_meat", "chicken", ["鸡肉"], "教材指鸡肉食物，原图为活鸡刨土"),
    ("sweet_candy", "sweet", ["糖果"], "G1指糖果，原图为草莓甜"),
    ("drink_beverage", "drink", ["饮料"], "G1指饮料，原图为遛狗后喝水"),
    ("water_noun", "water", ["水"], "G1指饮用水，原图为给植物浇水"),
    ("cool_stylish", "cool", ["酷帅的"], "G2指酷帅的，原图为凉爽微风"),
    ("skip_rope", "skip", ["跳绳"], "教材指跳绳，原图为没吃早饭"),
    ("card_greeting", "card", ["卡片"], "教材指贺卡/卡片，原图为刷银行卡"),
    ("poor_pitiful", "poor", ["可怜的"], "G1指可怜的，原图为贫困家庭"),
    ("lie_falsehood", "lie", ["谎言"], "教材指谎言，原图为躺在草地上"),
    ("pick_up", "pick", ["捡起"], "G2指捡起，原图为挑选窗帘颜色"),
    ("pick_pluck", "pick", ["采；摘"], "G2指采摘，原图为挑选窗帘颜色"),
    ("giant", "giant", ["巨人"], "教材指巨人，原图为巨大的南瓜"),
    ("slide_playground", "slide", ["滑梯"], "教材指滑梯，原图为桌面推盘子"),
    ("swing_playground", "swing", ["秋千"], "教材指秋千，原图为走路摆包"),
    ("roundabout_merry", "roundabout", ["旋转木马"], "教材指旋转木马，原图为交通环岛"),
    ("handle_object", "handle", ["提手"], "教材指茶壶/物体提手，原图为负责晚饭"),
    ("watch_wrist", "watch", ["手表"], "G2/G6指手表，原图为看鸭子"),
    ("skate_board", "skate", ["滑滑板", "滑（滑板）"], "G2/G4指滑滑板，原图为冰场滑冰"),
    ("fish_meat", "fish", ["鱼肉"], "G2指鱼肉食物，原图为桥下游鱼"),
    ("sure", "sure", ["当然"], "教材指当然，原图为询问是否确定"),
    ("sure_excl", "sure!", ["当然！"], "教材指当然，原图为询问是否确定"),
    ("light_lamp", "light", ["灯"], "G2指交通灯/灯，原图为窗帘阳光"),
    ("light_weight", "light", ["轻的"], "G6指轻的，原图为窗帘阳光"),
    ("sign_road", "sign", ["标志"], "教材指道路标志，原图为乌云预示下雨"),
    ("get_become", "get", ["变得"], "G4指变得，原图为收到生日围巾"),
    ("mouse_computer", "mouse", ["n. 鼠标"], "G5指电脑鼠标，原图为老鼠"),
    ("it_subject", "it", ["（学科）信息技术"], "G4指信息技术课IT，原图为代词it"),
    ("free_time", "free", ["空闲的"], "教材指空闲的，原图为免费饼干"),
    ("by_beside", "by", ["在......旁边"], "教材指在旁边，原图为由祖父制作"),
    ("study_room", "study", ["书房"], "教材指书房，原图为公交车上学英语"),
    ("country_rural", "country", ["乡村"], "G4指乡村，原图为国家旅行"),
    ("grow_become", "grow", ["逐渐变得；逐渐 成为"], "G6指逐渐变得，原图为种香草"),
    ("turn_become", "turn", ["（使）变成"], "教材指变成(如树叶变黄)，原图为拧门把手"),
    ("oil_cooking", "oil", ["食用油"], "G4指食用油，原图为原油油罐车"),
    ("way_road", "way", ["路线；道路"], "G4_b1指路线道路，原图为叠床单方法"),
    ("right_direction", "right", ["右边"], "教材指右边方向，原图为选对钥匙"),
    ("march_month", "march", ["三月"], "教材指三月，原图为乐队行进"),
    ("half_time", "half", ["（时间）……点半"], "教材指几点半，原图为半个三明治"),
    ("quarter_time", "quarter", ["15分钟；一刻钟"], "教材指一刻钟，原图为三明治切四份"),
    ("miss_title", "miss", ["小姐"], "G4指小姐称呼，原图为错过末班车"),
    ("miss_longing", "miss", ["想念"], "G6指想念，原图为错过末班车"),
    ("chinese_subject", "chinese", ["（学科）语文"], "教材指语文学科，原图为吃饺子"),
    ("triangle_instrument", "triangle", ["三角铁（打击乐器）"], "G4_u4指打击乐器三角铁，原图为折三角形纸"),
    ("hit_reach", "hit", ["达到（某水平）"], "G6指达到某水平/高温，原图为球撞栅栏"),
    ("square_plaza", "square", ["广场"], "G6指广场，原图为折正方形纸"),
    ("side_geometry", "side", ["边"], "教材指几何图形的边，原图为侧门泥靴"),
    ("second_time", "second", ["秒"], "教材指时间单位秒，原图为第二杯茶"),
    ("heat_verb", "heat", ["加热"], "G4指加热动作，原图为树下乘凉避暑"),
    ("view_scenery", "view", ["n. 景色"], "教材指景色，原图为个人看法"),
    ("stamp_verb", "stamp", ["v. 盖章；盖印"], "G5指盖章盖印，原图为信封贴邮票"),
    ("action_pose", "action", ["n. 动作"], "G5指肢体动作，原图为修漏水采取行动"),
    ("train_verb", "train", ["v. 训练"], "教材指训练，原图为赶末班火车"),
    ("scale_animal", "scale", ["n. 鳞片"], "教材指鳞片，原图为菜园规模"),
    ("treat_medical", "treat", ["v. 治疗"], "教材指医疗治疗，原图为善待小狗"),
    ("temperature_body", "temperature", ["n. 体温"], "G5指人体体温，原图为日落气温下降"),
    ("store_data", "store", ["v. 储存"], "G5指储存数据/物品，原图为街角商店"),
    ("symbol_char", "symbol", ["n. 符号"], "教材指电脑/数学符号，原图为老屋象征希望"),
    ("smart_tech", "smart", ["adj. 智能的"], "G5指智能科技，原图为聪明修架子"),
    ("save_money", "save", ["v. 储蓄"], "G5指储蓄存钱，原图为救生员救人"),
    ("interest_bank", "interest", ["n. 利息"], "教材指银行利息，原图为做饭兴趣"),
    ("point_tip", "point", ["尖端；点"], "教材指尖端/点，原图为提出好观点"),
    ("once_formerly", "once", ["曾经"], "教材指曾经，原图为两周浇一次水"),
    ("fair_light", "fair", ["（头发或皮肤）浅色的；白皙的"], "教材指浅色/白皙，原图为轮流玩保持公平"),
    ("hall_auditorium", "hall", ["礼堂；大厅"], "教材指礼堂大厅，原图为玄关放湿鞋"),
    ("host_presenter", "host", ["节目主持人"], "教材指节目主持人，原图为家庭主人端茶"),
    ("mean_signify", "mean", ["意思是"], "教材指意思是，原图为不是故意"),
    ("underground_metro", "underground", ["地铁；地下铁路系统"], "教材指地铁，原图为地下车库"),
    ("lift_elevator", "lift", ["电梯；升降机"], "教材指电梯，原图为抬箱子"),
    ("smoke_cigarette", "smoke", ["吸烟；抽烟"], "教材指吸烟，原图为吐司烤焦冒烟"),
    ("stay_remain", "stay", ["保持；继续是"], "教材指保持状态，原图为住湖边旅馆"),
    ("pay_attention_light", "pay", ["（与某些名词结合使 用，表示将要做或将付出某事物）"], "教材指pay attention等搭配，原图为刷卡买苹果"),
    ("pass_handover", "pass", ["给；递；传递"], "教材指递给传递，原图为路过面包店"),
    ("performance_stage", "performance", ["表演"], "教材指舞台演出表演，原图为足球赛表现"),
    ("drop_decrease", "drop", ["降低；减少"], "教材指温度降低减少，原图为掉钥匙"),
    ("degree_temp", "degree", ["度；度数"], "教材指温度度数，原图为大学学位"),
    ("reach_level", "reach", ["增加到；达到"], "教材指温度/数值达到，原图为到达车站"),
    ("sort_classify", "sort", ["整理；把......分类"], "教材指分类整理，原图为哪种音乐"),
    ("energy_power", "energy", ["能源"], "教材指清洁/电力能源，原图为午睡后有精力"),
    ("theory_science", "theory", ["学说；理论"], "教材指科学理论，原图为猜猫打翻杯子"),
    ("power_electric", "power", ["电；电力供应"], "教材指电力供应，原图为经理权力"),
    ("spend_time", "spend", ["花（时间）；度过"], "教材指花时间度过，原图为花钱买水果"),
    ("act_drama", "act", ["表演；行为"], "教材指戏剧表演，原图为水槽漏水采取行动"),
    ("character_role", "character", ["角色"], "教材指戏剧/故事角色，原图为开朗性格"),
    ("stage_theatre", "stage", ["舞台"], "教材指戏剧舞台，原图为烤蛋糕阶段"),
    ("level_standard", "level", ["水平；标准"], "教材指水平标准，原图为河水水位"),
]

def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s

items = []
seen_slugs = set()

def unique_slug(base: str) -> str:
    s = slugify(base)
    if s not in seen_slugs:
        seen_slugs.add(s)
        return s
    i = 2
    while f"{s}_{i}" in seen_slugs:
        i += 1
    seen_slugs.add(f"{s}_{i}")
    return f"{s}_{i}"

# 1. Ref items (P0 / P1)
for k, v in sorted(raw["ref"].items()):
    if k in REF_KEEP:
        continue
    slug = unique_slug(k)
    note = v["note"]
    m = re.search(r"参考词库词条\s*([^。]+)", note)
    ref_word = m.group(1).strip() if m else ""
    is_phrase = (" " in v["word"].strip()) or ("-" in v["word"]) or ("/" in v["word"])
    priority = "P0" if (not is_phrase or ref_word.lower() not in k.split()) else "P1"
    # More accurate P0 vs P1: if the phrase meaning is clearly distinct from single ref_word
    items.append({
        "key": slug,
        "category": "ref_phrase" if is_phrase else "ref_single",
        "priority": priority,
        "word": v["word"],
        "zh": " / ".join(v["zhs"]),
        "ref_word": ref_word,
        "current_ex_en": v["ex_en"],
        "reason": f"原图复用词条 `{ref_word}`，未准确表达 `{v['word']}` ({' / '.join(v['zhs'])})",
        "occurrences": [{"grade": o["grade"], "id": o["id"], "zh": o["zh"]} for o in v["occurrences"]],
        "image_path": f"output/fix-generated/{slug}.jpg",
        "scene_prompt": "",
    })

# 2. P2 polysemy items
for slug_base, word_key, zh_list, reason in P2_SPECS:
    if word_key not in raw["nonref_singles"]:
        print("WARN missing P2 key:", word_key)
        continue
    v = raw["nonref_singles"][word_key]
    occs = [o for o in v["occurrences"] if o["zh"] in zh_list]
    if not occs:
        print("WARN no matching occs for:", word_key, zh_list, v["zhs"])
        continue
    slug = unique_slug(f"p2_{slug_base}")
    items.append({
        "key": slug,
        "category": "p2_polysemy",
        "priority": "P2",
        "word": v["word"],
        "zh": " / ".join(zh_list),
        "ref_word": "",
        "current_ex_en": v["ex_en"],
        "reason": reason,
        "occurrences": [{"grade": o["grade"], "id": o["id"], "zh": o["zh"]} for o in occs],
        "image_path": f"output/fix-generated/{slug}.jpg",
        "scene_prompt": "",
    })

# Mark our 3 already-calibrated samples!
CALIBRATED = {
    "hot_dog": "output/fix-samples/hot_dog.jpg",
    "ice_cream": "output/fix-samples/ice_cream.jpg",
    "red_envelope": "output/fix-samples/red_envelope.jpg",
}
for it in items:
    if it["key"] in CALIBRATED:
        it["image_path"] = CALIBRATED[it["key"]]
        it["status"] = "calibrated"
    else:
        it["status"] = "pending"

summary = {
    "total_unique_images": len(items),
    "total_occurrences": sum(len(x["occurrences"]) for x in items),
    "ref_items": sum(1 for x in items if x["category"].startswith("ref_")),
    "ref_occurrences": sum(len(x["occurrences"]) for x in items if x["category"].startswith("ref_")),
    "p2_items": sum(1 for x in items if x["category"] == "p2_polysemy"),
    "p2_occurrences": sum(len(x["occurrences"]) for x in items if x["category"] == "p2_polysemy"),
    "ref_kept_as_is": len(REF_KEEP),
    "calibrated_ready": len(CALIBRATED),
}

out = {
    "style_prefix": (
        "Mid-century modern flat gouache children's picture-book illustration with subtle matte paper-grain texture, "
        "lineless soft painted shapes (strictly NO black ink outlines, NO comic strokes), "
        "muted warm vintage color palette (warm cream/ivory background, terracotta red-orange, sage/olive green, "
        "dusty denim blue, ochre/mustard yellow, warm wood brown, deep navy accents), cozy sunlit warmth, "
        "centered uncluttered 1:1 square composition readable at thumbnail size. "
        "STRICTLY NO TEXT, NO LETTERS, NO NUMBERS, NO LABELS, NO WATERMARKS, NO BORDERS. SCENE: "
    ),
    "summary": summary,
    "items": items,
}
(OUT_DIR / "manifest_skeleton.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("Summary:", json.dumps(summary, ensure_ascii=False, indent=2))
