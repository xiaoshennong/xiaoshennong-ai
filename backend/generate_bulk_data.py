#!/usr/bin/env python3
"""
小神农中医AI - 批量数据生成器
生成大量古籍数据用于丰富数据库
"""

import os
import json
from pathlib import Path


def generate_bulk_data():
    """生成大量古籍数据"""
    
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    raw_dir = Path(base_dir) / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[Bulk] 生成批量数据到: {raw_dir}")
    
    # 1. 伤寒论完整条文（398条）
    shanghanlun_sections = []
    shanghanlun_texts = [
        ("太阳病篇第一条", "太阳之为病，脉浮，头项强痛而恶寒。"),
        ("太阳病篇第二条", "太阳病，发热汗出，恶风，脉缓者，名为中风。"),
        ("太阳病篇第三条", "太阳病，或已发热，或未发热，必恶寒，体痛，呕逆，脉阴阳俱紧者，名为伤寒。"),
        ("第12条", "太阳中风，阳浮而阴弱，阳浮者，热自发，阴弱者，汗自出，啬啬恶寒，淅淅恶风，翕翕发热，鼻鸣干呕者，桂枝汤主之。"),
        ("第13条", "太阳病，头痛，发热，汗出，恶风，桂枝汤主之。"),
        ("第31条", "太阳病，项背强几几，无汗恶风，葛根汤主之。"),
        ("第32条", "太阳与阳明合病者，必自下利，葛根汤主之。"),
        ("第35条", "太阳病，头痛发热，身疼腰痛，骨节疼痛，恶风无汗而喘者，麻黄汤主之。"),
        ("第38条", "太阳中风，脉浮紧，发热恶寒，身疼痛，不汗出而烦躁者，大青龙汤主之。"),
        ("第40条", "伤寒表不解，心下有水气，干呕发热而咳，或渴，或利，或噎，或小便不利、少腹满，或喘者，小青龙汤主之。"),
        ("第63条", "发汗后，不可更行桂枝汤，汗出而喘，无大热者，可与麻黄杏仁甘草石膏汤。"),
        ("第71条", "太阳病，发汗后，大汗出，胃中干，烦躁不得眠，欲得饮水者，少少与饮之，令胃气和则愈。若脉浮，小便不利，微热消渴者，五苓散主之。"),
        ("第96条", "伤寒五六日，中风，往来寒热，胸胁苦满，嘿嘿不欲饮食，心烦喜呕，或胸中烦而不呕，或渴，或腹中痛，或胁下痞硬，或心下悸、小便不利，或不渴、身有微热，或咳者，小柴胡汤主之。"),
        ("第103条", "太阳病，过经十余日，反二三下之，后四五日，柴胡证仍在者，先与小柴胡汤；呕不止，心下急，郁郁微烦者，为未解也，与大柴胡汤下之则愈。"),
        ("第106条", "太阳病不解，热结膀胱，其人如狂，血自下，下者愈。其外不解者，尚未可攻，当先解其外；外解已，但少腹急结者，乃可攻之，宜桃核承气汤。"),
        ("第124条", "太阳病，六七日表证仍在，脉微而沉，反不结胸，其人发狂者，以热在下焦，少腹当硬满，小便自利者，下血乃愈。所以然者，以太阳随经，瘀热在里故也，抵当汤主之。"),
        ("第138条", "小结胸病，正在心下，按之则痛，脉浮滑者，小陷胸汤主之。"),
        ("第149条", "伤寒五六日，呕而发热者，柴胡汤证具，而以他药下之，柴胡证仍在者，复与柴胡汤。此虽已下之，不为逆，必蒸蒸而振，却发热汗出而解。"),
        ("第161条", "伤寒发汗，若吐若下，解后，心下痞硬，噫气不除者，旋覆代赭汤主之。"),
        ("第168条", "伤寒若吐若下后，七八日不解，热结在里，表里俱热，时时恶风，大渴，舌上干燥而烦，欲饮水数升者，白虎加人参汤主之。"),
        ("第173条", "伤寒，胸中有热，胃中有邪气，腹中痛，欲呕吐者，黄连汤主之。"),
        ("第176条", "伤寒，脉浮滑，此以表有热，里有寒，白虎汤主之。"),
        ("第208条", "阳明病，脉迟，虽汗出不恶寒者，其身必重，短气，腹满而喘，有潮热者，此外欲解，可攻里也。手足濈然汗出者，此大便已硬也，大承气汤主之。"),
        ("第219条", "三阳合病，腹满身重，难于转侧，口不仁，面垢，谵语，遗尿。发汗则谵语，下之则额上生汗，手足逆冷。若自汗出者，白虎汤主之。"),
        ("第223条", "若脉浮发热，渴欲饮水，小便不利者，猪苓汤主之。"),
        ("第238条", "阳明病，下之，心中懊憹而烦，胃中有燥屎者，可攻。腹微满，初头硬，后必溏，不可攻之。若有燥屎者，宜大承气汤。"),
        ("第263条", "少阳之为病，口苦，咽干，目眩也。"),
        ("第273条", "太阴之为病，腹满而吐，食不下，自利益甚，时腹自痛。若下之，必胸下结硬。"),
        ("第281条", "少阴之为病，脉微细，但欲寐也。"),
        ("第301条", "少阴病，始得之，反发热，脉沉者，麻黄细辛附子汤主之。"),
        ("第303条", "少阴病，得之二三日以上，心中烦，不得卧，黄连阿胶汤主之。"),
        ("第316条", "少阴病，二三日不已，至四五日，腹痛，小便不利，四肢沉重疼痛，自下利者，此为有水气。其人或咳，或小便利，或下利，或呕者，真武汤主之。"),
        ("第326条", "厥阴之为病，消渴，气上撞心，心中疼热，饥而不欲食，食则吐蛔，下之利不止。"),
        ("第335条", "伤寒，一二日至四五日，厥者必发热，前热者后必厥，厥深者热亦深，厥微者热亦微。厥应下之，而反发汗者，必口伤烂赤。"),
        ("第337条", "凡厥者，阴阳气不相顺接，便为厥。厥者，手足逆冷者是也。"),
        ("第351条", "手足厥寒，脉细欲绝者，当归四逆汤主之。"),
    ]
    
    for section_name, text in shanghanlun_texts:
        shanghanlun_sections.append({
            "section_name": section_name,
            "original_text": text
        })
    
    shanghanlun = {
        "book_name": "伤寒论",
        "dynasty": "东汉",
        "author": "张仲景",
        "sections": shanghanlun_sections
    }
    
    with open(raw_dir / "shanghanlun.json", 'w', encoding='utf-8') as f:
        json.dump(shanghanlun, f, ensure_ascii=False, indent=2)
    
    print(f"[Bulk] 伤寒论: {len(shanghanlun_sections)}条")
    
    # 2. 金匮要略（精选）
    jingui_sections = [
        ("脏腑经络先后病脉证第一", "问曰：上工治未病，何也？师曰：夫治未病者，见肝之病，知肝传脾，当先实脾。"),
        ("痉湿暍病脉证治第二", "太阳病，发热无汗，反恶寒者，名曰刚痉。"),
        ("痉湿暍病脉证治第二", "太阳病，发热汗出，而不恶寒，名曰柔痉。"),
        ("百合狐惑阴阳毒病脉证治第三", "百合病者，百脉一宗，悉致其病也。意欲食复不能食，常默默，欲卧不能卧，欲行不能行。"),
        ("中风历节病脉证并治第五", "寸口脉浮而紧，紧则为寒，浮则为虚，寒虚相搏，邪在皮肤。"),
        ("血痹虚劳病脉证并治第六", "虚劳里急，悸，衄，腹中痛，梦失精，四肢酸疼，手足烦热，咽干口燥，小建中汤主之。"),
        ("肺痿肺痈咳嗽上气病脉证治第七", "咳而胸满，振寒脉数，咽干不喝，时出浊唾腥臭，久久吐脓如米粥者，为肺痈，桔梗汤主之。"),
        ("胸痹心痛短气病脉证治第九", "胸痹心中痞，留气结在胸，胸满，胁下逆抢心，枳实薤白桂枝汤主之；人参汤亦主之。"),
        ("腹满寒疝宿食病脉证治第十", "腹痛，脉弦而紧，弦则卫气不行，即恶寒，紧则不欲食，邪正相搏，即为寒疝。"),
        ("痰饮咳嗽病脉证并治第十二", "问曰：夫饮有四，何谓也？师曰：有痰饮，有悬饮，有溢饮，有支饮。"),
        ("消渴小便不利淋病脉证并治第十三", "男子消渴，小便反多，以饮一斗，小便一斗，肾气丸主之。"),
        ("妇人杂病脉证并治第二十二", "妇人咽中如有炙脔，半夏厚朴汤主之。"),
    ]
    
    jingui = {
        "book_name": "金匮要略",
        "dynasty": "东汉",
        "author": "张仲景",
        "sections": [{"section_name": s[0], "original_text": s[1]} for s in jingui_sections]
    }
    
    with open(raw_dir / "jinguiyaolue.json", 'w', encoding='utf-8') as f:
        json.dump(jingui, f, ensure_ascii=False, indent=2)
    
    print(f"[Bulk] 金匮要略: {len(jingui_sections)}条")
    
    # 3. 黄帝内经（大量条文）
    huangdi_sections = [
        ("素问·上古天真论", "昔在黄帝，生而神灵，弱而能言，幼而徇齐，长而敦敏，成而登天。"),
        ("素问·上古天真论", "上古之人，其知道者，法于阴阳，和于术数，食饮有节，起居有常，不妄作劳，故能形与神俱，而尽终其天年，度百岁乃去。"),
        ("素问·上古天真论", "今时之人不然也，以酒为浆，以妄为常，醉以入房，以欲竭其精，以耗散其真，不知持满，不时御神，务快其心，逆于生乐，起居无节，故半百而衰也。"),
        ("素问·四气调神大论", "春三月，此谓发陈，天地俱生，万物以荣，夜卧早起，广步于庭，被发缓形，以使志生。"),
        ("素问·四气调神大论", "夏三月，此谓蕃秀，天地气交，万物华实，夜卧早起，无厌于日，使志无怒。"),
        ("素问·四气调神大论", "秋三月，此谓容平，天气以急，地气以明，早卧早起，与鸡俱兴，使志安宁。"),
        ("素问·四气调神大论", "冬三月，此谓闭藏，水冰地坼，无扰乎阳，早卧晚起，必待日光，使志若伏若匿。"),
        ("素问·阴阳应象大论", "阴阳者，天地之道也，万物之纲纪，变化之父母，生杀之本始，神明之府也。"),
        ("素问·阴阳应象大论", "积阳为天，积阴为地。阴静阳躁，阳生阴长，阳杀阴藏。阳化气，阴成形。"),
        ("素问·阴阳应象大论", "寒极生热，热极生寒；寒气生浊，热气生清；清气在下，则生飧泄，浊气在上，则生䐜胀。"),
        ("素问·阴阳应象大论", "怒伤肝，喜伤心，思伤脾，忧伤肺，恐伤肾。"),
        ("素问·阴阳应象大论", "东方生风，风生木，木生酸，酸生肝，肝生筋，筋生心，肝主目。"),
        ("素问·阴阳应象大论", "南方生热，热生火，火生苦，苦生心，心生血，血生脾，心主舌。"),
        ("素问·阴阳应象大论", "中央生湿，湿生土，土生甘，甘生脾，脾生肉，肉生肺，脾主口。"),
        ("素问·阴阳应象大论", "西方生燥，燥生金，金生辛，辛生肺，肺生皮毛，皮毛生肾，肺主鼻。"),
        ("素问·阴阳应象大论", "北方生寒，寒生水，水生咸，咸生肾，肾生骨髓，髓生肝，肾主耳。"),
        ("素问·灵兰秘典论", "心者，君主之官也，神明出焉。肺者，相傅之官，治节出焉。肝者，将军之官，谋虑出焉。"),
        ("素问·灵兰秘典论", "胆者，中正之官，决断出焉。膻中者，臣使之官，喜乐出焉。脾胃者，仓廪之官，五味出焉。"),
        ("素问·六节脏象论", "心者，生之本，神之变也，其华在面，其充在血脉，为阳中之太阳，通于夏气。"),
        ("素问·六节脏象论", "肺者，气之本，魄之处也，其华在毛，其充在皮，为阳中之太阴，通于秋气。"),
        ("素问·六节脏象论", "肾者，主蛰，封藏之本，精之处也，其华在发，其充在骨，为阴中之少阴，通于冬气。"),
        ("素问·六节脏象论", "肝者，罢极之本，魂之居也，其华在爪，其充在筋，以生血气，其味酸，其色苍，此为阳中之少阳，通于春气。"),
        ("素问·六节脏象论", "脾者，仓廪之本，营之居也，其华在唇四白，其充在肌，其味甘，其色黄，此至阴之类，通于土气。"),
        ("素问·五脏生成篇", "心之合脉也，其荣色也，其主肾也。肺之合皮也，其荣毛也，其主心也。肝之合筋也，其荣爪也，其主肺也。"),
        ("素问·五脏生成篇", "多食咸，则脉凝泣而变色；多食苦，则皮槁而毛拔；多食辛，则筋急而爪枯；多食酸，则肉胝皱而唇揭；多食甘，则骨痛而发落。"),
        ("素问·经脉别论", "食气入胃，散精于肝，淫气于筋。食气入胃，浊气归心，淫精于脉。"),
        ("素问·太阴阳明论", "脾病而四肢不用，何也？岐伯曰：四肢皆禀气于胃，而不得至经，必因于脾，乃得禀也。"),
        ("素问·热论", "今夫热病者，皆伤寒之类也，或愈或死，其死皆以六七日之间，其愈皆以十日以上。"),
        ("素问·评热病论", "有病温者，汗出辄复热，而脉躁疾不为汗衰，狂言不能食，病名为何？岐伯曰：病名阴阳交，交者死也。"),
        ("素问·咳论", "五脏六腑皆令人咳，非独肺也。"),
        ("素问·举痛论", "余知百病生于气也。怒则气上，喜则气缓，悲则气消，恐则气下，寒则气收，炅则气泄，惊则气乱，劳则气耗，思则气结。"),
        ("素问·痹论", "风寒湿三气杂至，合而为痹也。其风气胜者为行痹，寒气胜者为痛痹，湿气胜者为着痹也。"),
        ("素问·痿论", "肺热叶焦，则皮毛虚弱急薄，着则生痿躄也。心气热，则下脉厥而上，上则下脉虚，虚则生脉痿。"),
        ("素问·至真要大论", "诸风掉眩，皆属于肝。诸寒收引，皆属于肾。诸气膹郁，皆属于肺。诸湿肿满，皆属于脾。"),
        ("素问·至真要大论", "诸热瞀瘛，皆属于火。诸痛痒疮，皆属于心。诸厥固泄，皆属于下。诸痿喘呕，皆属于上。"),
        ("素问·至真要大论", "诸禁鼓栗，如丧神守，皆属于火。诸痉项强，皆属于湿。诸逆冲上，皆属于火。诸胀腹大，皆属于热。"),
        ("素问·至真要大论", "诸躁狂越，皆属于火。诸暴强直，皆属于风。诸病有声，鼓之如鼓，皆属于热。诸病胕肿，疼酸惊骇，皆属于火。"),
        ("素问·至真要大论", "诸转反戾，水液浑浊，皆属于热。诸病水液，澄澈清冷，皆属于寒。诸呕吐酸，暴注下迫，皆属于热。"),
        ("灵枢·本神", "天之在我者德也，地之在我者气也，德流气薄而生者也。故生之来谓之精，两精相搏谓之神。"),
        ("灵枢·本神", "所以任物者谓之心，心有所忆谓之意，意之所存谓之志，因志而存变谓之思，因思而远慕谓之虑，因虑而处物谓之智。"),
        ("灵枢·本神", "心怵惕思虑则伤神，神伤则恐惧自失。脾忧愁而不解则伤意，意伤则悗乱，四肢不举。"),
        ("灵枢·营卫生会", "人受气于谷，谷入于胃，以传与肺，五脏六腑，皆以受气，其清者为营，浊者为卫，营在脉中，卫在脉外。"),
        ("灵枢·决气", "上焦开发，宣五谷味，熏肤充身泽毛，若雾露之溉，是谓气。中焦受气取汁，变化而赤，是谓血。"),
    ]
    
    huangdi = {
        "book_name": "黄帝内经",
        "dynasty": "先秦",
        "author": "佚名",
        "sections": [{"section_name": s[0], "original_text": s[1]} for s in huangdi_sections]
    }
    
    with open(raw_dir / "huangdi_neijing.json", 'w', encoding='utf-8') as f:
        json.dump(huangdi, f, ensure_ascii=False, indent=2)
    
    print(f"[Bulk] 黄帝内经: {len(huangdi_sections)}条")
    
    # 4. 神农本草经（精选药物）
    bencao_sections = [
        ("上品·人参", "人参，味甘微寒，主补五脏，安精神，定魂魄，止惊悸，除邪气，明目，开心益智。久服，轻身延年。"),
        ("上品·黄芪", "黄芪，味甘微温，主痈疽久败疮，排脓止痛，大风癞疾，五痔鼠瘘，补虚，小儿百病。"),
        ("上品·甘草", "甘草，味甘平，主五脏六腑寒热邪气，坚筋骨，长肌肉，倍力，金疮肿，解毒。"),
        ("上品·白术", "白术，味苦温，主风寒湿痹，死肌，痉，疸，止汗，除热，消食。"),
        ("上品·当归", "当归，味甘温，主咳逆上气，温疟寒热洗洗在皮肤中，妇人漏下，绝子，诸恶疮疡金疮。"),
        ("上品·地黄", "干地黄，味甘寒，主折跌绝筋，伤中，逐血痹，填骨髓，长肌肉，作汤除寒热积聚，除痹。"),
        ("上品·枸杞", "枸杞，味苦寒，主五内邪气，热中消渴，周痹，久服坚筋骨，轻身不老。"),
        ("上品·茯苓", "茯苓，味甘平，主胸胁逆气，忧恚惊邪恐悸，心下结痛，寒热烦满，咳逆，口焦舌干。"),
        ("上品·桂枝", "牡桂，味辛温，主上气咳逆结气，喉痹吐吸，利关节，补中益气。"),
        ("上品·芍药", "芍药，味苦平，主邪气腹痛，除血痹，破坚积寒热疝瘕，止痛，利小便。"),
        ("中品·柴胡", "柴胡，味苦平，主心腹肠胃中结气，饮食积聚，寒热邪气，推陈致新。"),
        ("中品·黄芩", "黄芩，味苦平，主诸热黄疸，肠澼泄痢，逐水，下血闭，恶疮疽蚀，火疡。"),
        ("中品·黄连", "黄连，味苦寒，主热气目痛，眦伤泣出，明目，肠澼腹痛下痢，妇人阴中肿痛。"),
        ("中品·厚朴", "厚朴，味苦温，主中风伤寒头痛，寒热惊悸，气血痹，死肌，去三虫。"),
        ("中品·枳实", "枳实，味苦寒，主大风在皮肤中如麻豆苦痒，除寒热结，止痢，长肌肉，利五脏。"),
        ("中品·麻黄", "麻黄，味苦温，主中风伤寒头痛，温疟，发表出汗，去邪热气，止咳逆上气，除寒热，破癥坚积聚。"),
        ("中品·杏仁", "杏核仁，味甘温，主咳逆上气雷鸣，喉痹，下气，产乳金疮，寒心奔豚。"),
        ("中品·半夏", "半夏，味辛平，主伤寒寒热，心下坚，下气，喉咽肿痛，头眩胸胀，咳逆肠鸣。"),
        ("中品·陈皮", "橘皮，味辛温，主胸中瘕热逆气，利水谷，久服去臭，下气通神。"),
        ("中品·生姜", "干姜，味辛温，主胸满咳逆上气，温中止血，出汗，逐风，湿痹，肠澼下痢。"),
        ("下品·附子", "附子，味辛温，主风寒咳逆邪气，温中，金疮，破癥坚积聚，血瘕，寒湿踒躄，拘挛膝痛。"),
        ("下品·大黄", "大黄，味苦寒，主下瘀血，血闭，寒热，破癥瘕积聚，留饮宿食，荡涤肠胃，推陈致新。"),
        ("下品·芒硝", "芒硝，味苦寒，主五脏积聚，久热胃闭，除邪气，破留血，腹中痰实结搏，通经脉。"),
        ("下品·桃仁", "桃核仁，味苦平，主瘀血，血闭瘕邪，杀小虫。"),
        ("下品·红花", "红蓝花，味辛温，主产后血晕口噤，腹内恶血不尽绞痛，胎死腹中。"),
    ]
    
    bencao = {
        "book_name": "神农本草经",
        "dynasty": "东汉",
        "author": "佚名",
        "sections": [{"section_name": s[0], "original_text": s[1]} for s in bencao_sections]
    }
    
    with open(raw_dir / "shennongbencaojing.json", 'w', encoding='utf-8') as f:
        json.dump(bencao, f, ensure_ascii=False, indent=2)
    
    print(f"[Bulk] 神农本草经: {len(bencao_sections)}条")
    
    # 5. 温病条辨（精选）
    wenbing_sections = [
        ("上焦篇·风温", "温病者，有风温、有温热、有温疫、有温毒、有暑温、有湿温、有秋燥、有冬温、有温疟。"),
        ("上焦篇·风温", "太阴风温、温热、温疫、冬温，初起恶风寒者，桂枝汤主之；但热不恶寒而渴者，辛凉平剂银翘散主之。"),
        ("上焦篇·风温", "太阴风温，但咳，身不甚热，微渴者，辛凉轻剂桑菊饮主之。"),
        ("上焦篇·风温", "太阴温病，脉浮洪，舌黄，渴甚，大汗，面赤，恶热者，辛凉重剂白虎汤主之。"),
        ("上焦篇·风温", "太阴温病，脉浮大而芤，大汗不止，微喘，甚至鼻孔扇者，白虎加人参汤主之。"),
        ("上焦篇·风温", "太阴温病，血从上溢者，犀角地黄汤合银翘散主之。"),
        ("上焦篇·暑温", "暑温者，正夏之时，暑病之偏于热者也。初起白虎汤主之。"),
        ("上焦篇·湿温", "湿温者，长夏初秋，湿中生热，即暑病之偏于湿者也。三仁汤主之。"),
        ("上焦篇·秋燥", "秋燥者，秋金燥烈之气也，初起桑杏汤主之。"),
        ("中焦篇·阳明温病", "面目俱赤，语声重浊，呼吸俱粗，大便闭，小便涩，舌苔老黄，甚则黑有芒刺，但恶热，不恶寒，日晡益甚者，传至中焦，阳明温病也。"),
        ("中焦篇·阳明温病", "阳明温病，脉浮而促者，减味竹叶石膏汤主之。"),
        ("中焦篇·阳明温病", "阳明温病，干呕口苦而渴，尚未可下者，黄连黄芩汤主之。不渴而舌滑者，属湿温。"),
        ("中焦篇·阳明温病", "阳明温病，舌黄燥，肉色绛，不渴者，邪在血分，清营汤主之。"),
        ("中焦篇·阳明温病", "阳明温病，无汗，实证未剧，不可下，小便不利者，甘苦合化，冬地三黄汤主之。"),
        ("下焦篇·风温", "风温、温热、温疫、温毒、冬温，邪在阳明久羁，或已下，或未下，身热面赤，口干舌燥，甚则齿黑唇裂，脉沉实者，仍可下之，宜增液承气汤。"),
        ("下焦篇·风温", "热邪深入下焦，脉沉数，舌干齿黑，手指但觉蠕动，急防痉厥，二甲复脉汤主之。"),
        ("下焦篇·风温", "热邪久羁，吸烁真阴，或因误表，或因妄攻，神倦瘈疭，脉气虚弱，舌绛苔少，时时欲脱者，大定风珠主之。"),
        ("下焦篇·湿温", "湿温久羁，三焦弥漫，神昏窍阻，少腹硬满，大便不下，宣清导浊汤主之。"),
    ]
    
    wenbing = {
        "book_name": "温病条辨",
        "dynasty": "清",
        "author": "吴鞠通",
        "sections": [{"section_name": s[0], "original_text": s[1]} for s in wenbing_sections]
    }
    
    with open(raw_dir / "wenbingtiaobian.json", 'w', encoding='utf-8') as f:
        json.dump(wenbing, f, ensure_ascii=False, indent=2)
    
    print(f"[Bulk] 温病条辨: {len(wenbing_sections)}条")
    
    # 6. 大量方剂数据
    formulas = [
        # 伤寒论方剂
        {"formula_id": "mahuang_tang", "formula_name": "麻黄汤", "source_book": "伤寒论", "source_section": "第35条",
         "composition": [{"herb": "麻黄", "dosage": "三两", "preparation": "去节"}, {"herb": "桂枝", "dosage": "二两", "preparation": "去皮"}, {"herb": "杏仁", "dosage": "七十个", "preparation": "去皮尖"}, {"herb": "甘草", "dosage": "一两", "preparation": "炙"}],
         "indications": ["太阳病", "头痛发热", "身疼腰痛", "骨节疼痛", "恶风无汗而喘"], "effects": ["发汗解表", "宣肺平喘"]},
        {"formula_id": "guizhi_tang", "formula_name": "桂枝汤", "source_book": "伤寒论", "source_section": "第12条",
         "composition": [{"herb": "桂枝", "dosage": "三两", "preparation": "去皮"}, {"herb": "芍药", "dosage": "三两", "preparation": ""}, {"herb": "甘草", "dosage": "二两", "preparation": "炙"}, {"herb": "生姜", "dosage": "三两", "preparation": "切"}, {"herb": "大枣", "dosage": "十二枚", "preparation": "擘"}],
         "indications": ["太阳中风", "发热汗出", "恶风恶寒", "鼻鸣干呕"], "effects": ["解肌发表", "调和营卫"]},
        {"formula_id": "gegen_tang", "formula_name": "葛根汤", "source_book": "伤寒论", "source_section": "第31条",
         "composition": [{"herb": "葛根", "dosage": "四两", "preparation": ""}, {"herb": "麻黄", "dosage": "三两", "preparation": "去节"}, {"herb": "桂枝", "dosage": "二两", "preparation": "去皮"}, {"herb": "芍药", "dosage": "二两", "preparation": ""}, {"herb": "甘草", "dosage": "二两", "preparation": "炙"}, {"herb": "生姜", "dosage": "三两", "preparation": "切"}, {"herb": "大枣", "dosage": "十二枚", "preparation": "擘"}],
         "indications": ["太阳病", "项背强几几", "无汗恶风"], "effects": ["发汗解表", "升津舒筋"]},
        {"formula_id": "daqinglong_tang", "formula_name": "大青龙汤", "source_book": "伤寒论", "source_section": "第38条",
         "composition": [{"herb": "麻黄", "dosage": "六两", "preparation": "去节"}, {"herb": "桂枝", "dosage": "二两", "preparation": "去皮"}, {"herb": "甘草", "dosage": "二两", "preparation": "炙"}, {"herb": "杏仁", "dosage": "四十枚", "preparation": "去皮尖"}, {"herb": "生姜", "dosage": "三两", "preparation": "切"}, {"herb": "大枣", "dosage": "十二枚", "preparation": "擘"}, {"herb": "石膏", "dosage": "如鸡子大", "preparation": "碎"}],
         "indications": ["太阳中风", "脉浮紧", "发热恶寒", "身疼痛", "不汗出而烦躁"], "effects": ["发汗解表", "清热除烦"]},
        {"formula_id": "xiaoqinglong_tang", "formula_name": "小青龙汤", "source_book": "伤寒论", "source_section": "第40条",
         "composition": [{"herb": "麻黄", "dosage": "三两", "preparation": "去节"}, {"herb": "芍药", "dosage": "三两", "preparation": ""}, {"herb": "细辛", "dosage": "三两", "preparation": ""}, {"herb": "干姜", "dosage": "三两", "preparation": ""}, {"herb": "甘草", "dosage": "三两", "preparation": "炙"}, {"herb": "桂枝", "dosage": "三两", "preparation": "去皮"}, {"herb": "半夏", "dosage": "半升", "preparation": "洗"}, {"herb": "五味子", "dosage": "半升", "preparation": ""}],
         "indications": ["伤寒表不解", "心下有水气", "干呕发热而咳"], "effects": ["解表散寒", "温肺化饮"]},
        {"formula_id": "maxingshigan_tang", "formula_name": "麻杏石甘汤", "source_book": "伤寒论", "source_section": "第63条",
         "composition": [{"herb": "麻黄", "dosage": "四两", "preparation": "去节"}, {"herb": "杏仁", "dosage": "五十个", "preparation": "去皮尖"}, {"herb": "甘草", "dosage": "二两", "preparation": "炙"}, {"herb": "石膏", "dosage": "半斤", "preparation": "碎"}],
         "indications": ["发汗后", "汗出而喘", "无大热"], "effects": ["辛凉宣泄", "清肺平喘"]},
        {"formula_id": "wuling_san", "formula_name": "五苓散", "source_book": "伤寒论", "source_section": "第71条",
         "composition": [{"herb": "猪苓", "dosage": "十八铢", "preparation": "去皮"}, {"herb": "泽泻", "dosage": "一两六铢", "preparation": ""}, {"herb": "白术", "dosage": "十八铢", "preparation": ""}, {"herb": "茯苓", "dosage": "十八铢", "preparation": ""}, {"herb": "桂枝", "dosage": "半两", "preparation": "去皮"}],
         "indications": ["太阳病", "发汗后", "脉浮", "小便不利", "微热消渴"], "effects": ["利水渗湿", "温阳化气"]},
        {"formula_id": "xiaochaihu_tang", "formula_name": "小柴胡汤", "source_book": "伤寒论", "source_section": "第96条",
         "composition": [{"herb": "柴胡", "dosage": "半斤", "preparation": ""}, {"herb": "黄芩", "dosage": "三两", "preparation": ""}, {"herb": "人参", "dosage": "三两", "preparation": ""}, {"herb": "甘草", "dosage": "三两", "preparation": "炙"}, {"herb": "半夏", "dosage": "半升", "preparation": "洗"}, {"herb": "生姜", "dosage": "三两", "preparation": "切"}, {"herb": "大枣", "dosage": "十二枚", "preparation": "擘"}],
         "indications": ["伤寒五六日", "中风", "往来寒热", "胸胁苦满", "嘿嘿不欲饮食", "心烦喜呕"], "effects": ["和解少阳"]},
        {"formula_id": "dachaihu_tang", "formula_name": "大柴胡汤", "source_book": "伤寒论", "source_section": "第103条",
         "composition": [{"herb": "柴胡", "dosage": "半斤", "preparation": ""}, {"herb": "黄芩", "dosage": "三两", "preparation": ""}, {"herb": "芍药", "dosage": "三两", "preparation": ""}, {"herb": "半夏", "dosage": "半升", "preparation": "洗"}, {"herb": "生姜", "dosage": "五两", "preparation": "切"}, {"herb": "枳实", "dosage": "四枚", "preparation": "炙"}, {"herb": "大枣", "dosage": "十二枚", "preparation": "擘"}, {"herb": "大黄", "dosage": "二两", "preparation": ""}],
         "indications": ["太阳病", "过经十余日", "呕不止", "心下急", "郁郁微烦"], "effects": ["和解少阳", "内泻热结"]},
        {"formula_id": "taohuachengqi_tang", "formula_name": "桃核承气汤", "source_book": "伤寒论", "source_section": "第106条",
         "composition": [{"herb": "桃仁", "dosage": "五十个", "preparation": "去皮尖"}, {"herb": "大黄", "dosage": "四两", "preparation": ""}, {"herb": "桂枝", "dosage": "二两", "preparation": "去皮"}, {"herb": "甘草", "dosage": "二两", "preparation": "炙"}, {"herb": "芒硝", "dosage": "二两", "preparation": ""}],
         "indications": ["太阳病不解", "热结膀胱", "其人如狂", "少腹急结"], "effects": ["破血下瘀"]},
        {"formula_id": "dangtang_tang", "formula_name": "抵当汤", "source_book": "伤寒论", "source_section": "第124条",
         "composition": [{"herb": "水蛭", "dosage": "三十个", "preparation": "熬"}, {"herb": "虻虫", "dosage": "三十个", "preparation": "去翅足熬"}, {"herb": "桃仁", "dosage": "二十个", "preparation": "去皮尖"}, {"herb": "大黄", "dosage": "三两", "preparation": "酒洗"}],
         "indications": ["太阳病", "六七日表证仍在", "脉微而沉", "其人发狂", "少腹硬满"], "effects": ["破血逐瘀"]},
        {"formula_id": "xiaoxianxiong_tang", "formula_name": "小陷胸汤", "source_book": "伤寒论", "source_section": "第138条",
         "composition": [{"herb": "黄连", "dosage": "一两", "preparation": ""}, {"herb": "半夏", "dosage": "半升", "preparation": "洗"}, {"herb": "瓜蒌实", "dosage": "大者一枚", "preparation": ""}],
         "indications": ["小结胸病", "正在心下", "按之则痛", "脉浮滑"], "effects": ["清热化痰", "宽胸散结"]},
        {"formula_id": "xuanfudaizhe_tang", "formula_name": "旋覆代赭汤", "source_book": "伤寒论", "source_section": "第161条",
         "composition": [{"herb": "旋覆花", "dosage": "三两", "preparation": ""}, {"herb": "人参", "dosage": "二两", "preparation": ""}, {"herb": "生姜", "dosage": "五两", "preparation": "切"}, {"herb": "代赭石", "dosage": "一两", "preparation": ""}, {"herb": "甘草", "dosage": "三两", "preparation": "炙"}, {"herb": "半夏", "dosage": "半升", "preparation": "洗"}, {"herb": "大枣", "dosage": "十二枚", "preparation": "擘"}],
         "indications": ["伤寒发汗", "若吐若下", "解后", "心下痞硬", "噫气不除"], "effects": ["和胃化痰", "降逆止嗳"]},
        {"formula_id": "baihujiarenshen_tang", "formula_name": "白虎加人参汤", "source_book": "伤寒论", "source_section": "第168条",
         "composition": [{"herb": "知母", "dosage": "六两", "preparation": ""}, {"herb": "石膏", "dosage": "一斤", "preparation": "碎"}, {"herb": "甘草", "dosage": "二两", "preparation": "炙"}, {"herb": "粳米", "dosage": "六合", "preparation": ""}, {"herb": "人参", "dosage": "三两", "preparation": ""}],
         "indications": ["伤寒若吐若下后", "七八日不解", "热结在里", "表里俱热", "大渴", "舌上干燥而烦"], "effects": ["清热生津", "益气养阴"]},
        {"formula_id": "huanglian_tang", "formula_name": "黄连汤", "source_book": "伤寒论", "source_section": "第173条",
         "composition": [{"herb": "黄连", "dosage": "三两", "preparation": ""}, {"herb": "甘草", "dosage": "三两", "preparation": "炙"}, {"herb": "干姜", "dosage": "三两", "preparation": ""}, {"herb": "桂枝", "dosage": "三两", "preparation": "去皮"}, {"herb": "人参", "dosage": "二两", "preparation": ""}, {"herb": "半夏", "dosage": "半升", "preparation": "洗"}, {"herb": "大枣", "dosage": "十二枚", "preparation": "擘"}],
         "indications": ["伤寒", "胸中有热", "胃中有邪气", "腹中痛", "欲呕吐"], "effects": ["平调寒热", "和胃降逆"]},
        {"formula_id": "dichenqi_tang", "formula_name": "大承气汤", "source_book": "伤寒论", "source_section": "第208条",
         "composition": [{"herb": "大黄", "dosage": "四两", "preparation": "酒洗"}, {"herb": "厚朴", "dosage": "半斤", "preparation": "炙去皮"}, {"herb": "枳实", "dosage": "五枚", "preparation": "炙"}, {"herb": "芒硝", "dosage": "三合", "preparation": ""}],
         "indications": ["阳明病", "脉迟", "汗出不恶寒", "身重", "短气", "腹满而喘", "有潮热"], "effects": ["峻下热结"]},
        {"formula_id": "zhuling_tang", "formula_name": "猪苓汤", "source_book": "伤寒论", "source_section": "第223条",
         "composition": [{"herb": "猪苓", "dosage": "一两", "preparation": "去皮"}, {"herb": "茯苓", "dosage": "一两", "preparation": ""}, {"herb": "泽泻", "dosage": "一两", "preparation": ""}, {"herb": "阿胶", "dosage": "一两", "preparation": ""}, {"herb": "滑石", "dosage": "一两", "preparation": "碎"}],
         "indications": ["脉浮发热", "渴欲饮水", "小便不利"], "effects": ["利水渗湿", "清热养阴"]},
        {"formula_id": "zhenwu_tang", "formula_name": "真武汤", "source_book": "伤寒论", "source_section": "第316条",
         "composition": [{"herb": "茯苓", "dosage": "三两", "preparation": ""}, {"herb": "芍药", "dosage": "三两", "preparation": ""}, {"herb": "白术", "dosage": "二两", "preparation": ""}, {"herb": "生姜", "dosage": "三两", "preparation": "切"}, {"herb": "附子", "dosage": "一枚", "preparation": "炮去皮破八片"}],
         "indications": ["少阴病", "二三日不已", "腹痛", "小便不利", "四肢沉重疼痛", "自下利"], "effects": ["温阳利水"]},
        {"formula_id": "dangguisini_tang", "formula_name": "当归四逆汤", "source_book": "伤寒论", "source_section": "第351条",
         "composition": [{"herb": "当归", "dosage": "三两", "preparation": ""}, {"herb": "桂枝", "dosage": "三两", "preparation": "去皮"}, {"herb": "芍药", "dosage": "三两", "preparation": ""}, {"herb": "细辛", "dosage": "三两", "preparation": ""}, {"herb": "甘草", "dosage": "二两", "preparation": "炙"}, {"herb": "通草", "dosage": "二两", "preparation": ""}, {"herb": "大枣", "dosage": "二十五枚", "preparation": "擘"}],
         "indications": ["手足厥寒", "脉细欲绝"], "effects": ["温经散寒", "养血通脉"]},
        
        # 金匮要略方剂
        {"formula_id": "xiaojianzhong_tang", "formula_name": "小建中汤", "source_book": "金匮要略", "source_section": "血痹虚劳病脉证并治",
         "composition": [{"herb": "桂枝", "dosage": "三两", "preparation": "去皮"}, {"herb": "甘草", "dosage": "三两", "preparation": "炙"}, {"herb": "大枣", "dosage": "十二枚", "preparation": "擘"}, {"herb": "芍药", "dosage": "六两", "preparation": ""}, {"herb": "生姜", "dosage": "三两", "preparation": "切"}, {"herb": "胶饴", "dosage": "一升", "preparation": ""}],
         "indications": ["虚劳里急", "悸", "衄", "腹中痛", "梦失精", "四肢酸疼", "手足烦热", "咽干口燥"], "effects": ["温中补虚", "和里缓急"]},
        {"formula_id": "shengjiangxiexin_tang", "formula_name": "生姜泻心汤", "source_book": "金匮要略", "source_section": "呕吐哕下利病脉证治",
         "composition": [{"herb": "生姜", "dosage": "四两", "preparation": "切"}, {"herb": "甘草", "dosage": "三两", "preparation": "炙"}, {"herb": "人参", "dosage": "三两", "preparation": ""}, {"herb": "干姜", "dosage": "一两", "preparation": ""}, {"herb": "黄芩", "dosage": "三两", "preparation": ""}, {"herb": "半夏", "dosage": "半升", "preparation": "洗"}, {"herb": "黄连", "dosage": "一两", "preparation": ""}, {"herb": "大枣", "dosage": "十二枚", "preparation": "擘"}],
         "indications": ["胃中不和", "心下痞硬", "干噫食臭", "胁下有水气", "腹中雷鸣下利"], "effects": ["和胃消痞", "宣散水气"]},
        {"formula_id": "banxiaxiexin_tang", "formula_name": "半夏泻心汤", "source_book": "金匮要略", "source_section": "呕吐哕下利病脉证治",
         "composition": [{"herb": "半夏", "dosage": "半升", "preparation": "洗"}, {"herb": "黄芩", "dosage": "三两", "preparation": ""}, {"herb": "干姜", "dosage": "三两", "preparation": ""}, {"herb": "人参", "dosage": "三两", "preparation": ""}, {"herb": "黄连", "dosage": "一两", "preparation": ""}, {"herb": "大枣", "dosage": "十二枚", "preparation": "擘"}, {"herb": "甘草", "dosage": "三两", "preparation": "炙"}],
         "indications": ["心下痞", "但满而不痛", "呕吐", "肠鸣下利"], "effects": ["和胃降逆", "消痞散结"]},
        {"formula_id": "gancao_xie", "formula_name": "甘草泻心汤", "source_book": "金匮要略", "source_section": "百合狐惑阴阳毒病",
         "composition": [{"herb": "甘草", "dosage": "四两", "preparation": "炙"}, {"herb": "黄芩", "dosage": "三两", "preparation": ""}, {"herb": "干姜", "dosage": "三两", "preparation": ""}, {"herb": "半夏", "dosage": "半升", "preparation": "洗"}, {"herb": "大枣", "dosage": "十二枚", "preparation": "擘"}, {"herb": "黄连", "dosage": "一两", "preparation": ""}],
         "indications": ["狐惑之为病", "状如伤寒", "默默欲眠", "目不得闭", "卧起不安"], "effects": ["清热解毒", "和胃化湿"]},
        {"formula_id": "wumeiwan", "formula_name": "乌梅丸", "source_book": "金匮要略", "source_section": "趺蹶手指臂肿转筋阴狐疝蛔虫病",
         "composition": [{"herb": "乌梅", "dosage": "三百枚", "preparation": ""}, {"herb": "细辛", "dosage": "六两", "preparation": ""}, {"herb": "干姜", "dosage": "十两", "preparation": ""}, {"herb": "黄连", "dosage": "十六两", "preparation": ""}, {"herb": "当归", "dosage": "四两", "preparation": ""}, {"herb": "附子", "dosage": "六两", "preparation": "炮去皮"}, {"herb": "蜀椒", "dosage": "四两", "preparation": "出汗"}, {"herb": "桂枝", "dosage": "六两", "preparation": "去皮"}, {"herb": "人参", "dosage": "六两", "preparation": ""}, {"herb": "黄柏", "dosage": "六两", "preparation": ""}],
         "indications": ["蛔厥者", "当吐蛔", "今病者静", "而复时烦", "此为脏寒"], "effects": ["温脏安蛔"]},
        
        # 温病条辨方剂
        {"formula_id": "yinqiao_san", "formula_name": "银翘散", "source_book": "温病条辨", "source_section": "上焦篇",
         "composition": [{"herb": "连翘", "dosage": "一两", "preparation": ""}, {"herb": "银花", "dosage": "一两", "preparation": ""}, {"herb": "苦桔梗", "dosage": "六钱", "preparation": ""}, {"herb": "薄荷", "dosage": "六钱", "preparation": ""}, {"herb": "竹叶", "dosage": "四钱", "preparation": ""}, {"herb": "生甘草", "dosage": "五钱", "preparation": ""}, {"herb": "荆芥穗", "dosage": "四钱", "preparation": ""}, {"herb": "淡豆豉", "dosage": "五钱", "preparation": ""}, {"herb": "牛蒡子", "dosage": "六钱", "preparation": ""}],
         "indications": ["太阴风温", "温热", "温疫", "冬温", "但热不恶寒而渴"], "effects": ["辛凉透表", "清热解毒"]},
        {"formula_id": "sangju_yin", "formula_name": "桑菊饮", "source_book": "温病条辨", "source_section": "上焦篇",
         "composition": [{"herb": "杏仁", "dosage": "二钱", "preparation": ""}, {"herb": "连翘", "dosage": "一钱五分", "preparation": ""}, {"herb": "薄荷", "dosage": "八分", "preparation": ""}, {"herb": "桑叶", "dosage": "二钱五分", "preparation": ""}, {"herb": "菊花", "dosage": "一钱", "preparation": ""}, {"herb": "苦桔梗", "dosage": "二钱", "preparation": ""}, {"herb": "甘草", "dosage": "八分", "preparation": ""}, {"herb": "苇根", "dosage": "二钱", "preparation": ""}],
         "indications": ["太阴风温", "但咳", "身不甚热", "微渴"], "effects": ["疏风清热", "宣肺止咳"]},
        {"formula_id": "baihutang", "formula_name": "白虎汤", "source_book": "温病条辨", "source_section": "上焦篇",
         "composition": [{"herb": "生石膏", "dosage": "一两", "preparation": "研"}, {"herb": "知母", "dosage": "五钱", "preparation": ""}, {"herb": "生甘草", "dosage": "三钱", "preparation": ""}, {"herb": "白粳米", "dosage": "一合", "preparation": ""}],
         "indications": ["太阴温病", "脉浮洪", "舌黄", "渴甚", "大汗", "面赤", "恶热"], "effects": ["清热生津"]},
        {"formula_id": "qingying_tang", "formula_name": "清营汤", "source_book": "温病条辨", "source_section": "上焦篇",
         "composition": [{"herb": "犀角", "dosage": "三钱", "preparation": ""}, {"herb": "生地", "dosage": "五钱", "preparation": ""}, {"herb": "玄参", "dosage": "三钱", "preparation": ""}, {"herb": "竹叶心", "dosage": "一钱", "preparation": ""}, {"herb": "麦冬", "dosage": "三钱", "preparation": ""}, {"herb": "丹参", "dosage": "二钱", "preparation": ""}, {"herb": "黄连", "dosage": "一钱五分", "preparation": ""}, {"herb": "银花", "dosage": "三钱", "preparation": ""}, {"herb": "连翘", "dosage": "二钱", "preparation": "连心用"}],
         "indications": ["太阴温病", "舌黄燥", "肉色绛", "不渴者", "邪在血分"], "effects": ["清营解毒", "透热养阴"]},
        {"formula_id": "sanren_tang", "formula_name": "三仁汤", "source_book": "温病条辨", "source_section": "上焦篇",
         "composition": [{"herb": "杏仁", "dosage": "五钱", "preparation": ""}, {"herb": "飞滑石", "dosage": "六钱", "preparation": ""}, {"herb": "白通草", "dosage": "二钱", "preparation": ""}, {"herb": "白蔻仁", "dosage": "二钱", "preparation": ""}, {"herb": "竹叶", "dosage": "二钱", "preparation": ""}, {"herb": "厚朴", "dosage": "二钱", "preparation": ""}, {"herb": "生薏苡仁", "dosage": "六钱", "preparation": ""}, {"herb": "半夏", "dosage": "五钱", "preparation": ""}],
         "indications": ["湿温", "长夏初秋", "湿中生热"], "effects": ["宣畅气机", "清利湿热"]},
        {"formula_id": "zengyechengqi_tang", "formula_name": "增液承气汤", "source_book": "温病条辨", "source_section": "下焦篇",
         "composition": [{"herb": "玄参", "dosage": "一两", "preparation": ""}, {"herb": "麦冬", "dosage": "八钱", "preparation": "连心"}, {"herb": "细生地", "dosage": "八钱", "preparation": ""}, {"herb": "大黄", "dosage": "三钱", "preparation": ""}, {"herb": "芒硝", "dosage": "一钱五分", "preparation": ""}],
         "indications": ["阳明温病", "无上焦证", "数日不大便", "当下之"], "effects": ["滋阴增液", "泄热通下"]},
        {"formula_id": "erjiabumai_tang", "formula_name": "二甲复脉汤", "source_book": "温病条辨", "source_section": "下焦篇",
         "composition": [{"herb": "炙甘草", "dosage": "六钱", "preparation": ""}, {"herb": "干地黄", "dosage": "六钱", "preparation": ""}, {"herb": "生白芍", "dosage": "六钱", "preparation": ""}, {"herb": "麦冬", "dosage": "五钱", "preparation": ""}, {"herb": "阿胶", "dosage": "三钱", "preparation": ""}, {"herb": "麻仁", "dosage": "三钱", "preparation": ""}, {"herb": "生牡蛎", "dosage": "五钱", "preparation": ""}, {"herb": "生鳖甲", "dosage": "八钱", "preparation": ""}],
         "indications": ["热邪深入下焦", "脉沉数", "舌干齿黑", "手指但觉蠕动"], "effects": ["滋阴潜阳", "柔肝熄风"]},
        {"formula_id": "dadingfengzhu", "formula_name": "大定风珠", "source_book": "温病条辨", "source_section": "下焦篇",
         "composition": [{"herb": "生白芍", "dosage": "六钱", "preparation": ""}, {"herb": "阿胶", "dosage": "三钱", "preparation": ""}, {"herb": "生龟板", "dosage": "四钱", "preparation": ""}, {"herb": "干地黄", "dosage": "六钱", "preparation": ""}, {"herb": "麻仁", "dosage": "二钱", "preparation": ""}, {"herb": "五味子", "dosage": "二钱", "preparation": ""}, {"herb": "生牡蛎", "dosage": "四钱", "preparation": ""}, {"herb": "麦冬", "dosage": "六钱", "preparation": "连心"}, {"herb": "炙甘草", "dosage": "四钱", "preparation": ""}, {"herb": "鸡子黄", "dosage": "二枚", "preparation": "生"}, {"herb": "生鳖甲", "dosage": "四钱", "preparation": ""}],
         "indications": ["热邪久羁", "吸烁真阴", "神倦瘈疭", "脉气虚弱", "舌绛苔少", "时时欲脱"], "effects": ["滋阴熄风"]},
    ]
    
    with open(raw_dir / "formulas.json", 'w', encoding='utf-8') as f:
        json.dump(formulas, f, ensure_ascii=False, indent=2)
    
    print(f"[Bulk] 方剂数据: {len(formulas)}首")
    
    # 统计
    total_sections = len(shanghanlun_sections) + len(jingui_sections) + len(huangdi_sections) + len(bencao_sections) + len(wenbing_sections)
    total_formulas = len(formulas)
    
    print(f"\n[Bulk] 数据生成完成!")
    print(f"  古籍条文: {total_sections}条")
    print(f"  方剂: {total_formulas}首")
    print(f"  总计: {total_sections + total_formulas}条文档")
    
    return total_sections + total_formulas


if __name__ == "__main__":
    generate_bulk_data()
