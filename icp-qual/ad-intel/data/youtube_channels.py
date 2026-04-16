"""YouTube Channel Profile Index — profile images for pitch report channel recommendations.

Each channel has `categories` (audience taxonomy) and a rough `subscribers` band
so the pitch generator can match channels to the brand's industry instead of
defaulting to kids/family content for every brand.

Category taxonomy:
  - kids               — pre-school / under-10 audience
  - family             — family-friendly content for adults with kids
  - general-entertainment — broad-appeal entertainment, mass reach
  - sports             — sports/athletics content
  - tech               — consumer tech reviews / dev / gadgets
  - beauty             — beauty / skincare / cosmetics
  - lifestyle          — lifestyle / wellness / personal development
  - food               — food / cooking / culinary
  - fitness            — fitness / workouts / training
  - science            — science / education / how-things-work
  - female-skewing     — channels with strong female audience
  - male-skewing       — channels with strong male audience
"""

import re

YOUTUBE_CHANNEL_PROFILES = {
    "ms rachel": {
        "channel_name": "Ms Rachel - Songs for Littles",
        "channel_url": "https://www.youtube.com/@msrachel",
        "image_url": "https://yt3.googleusercontent.com/C2nKGvtlPIpTO80svL80ZRRArA_512rEBMiZH6IWForDdVLd0SlVYQVObnmHxzVTeH9sOeNO=s240-c-k-c0x00ffffff-no-rj",
        "categories": ["kids", "family"],
        "subscribers": "15M+",
        "description": "Toddler-focused educational songs and language development",
    },
    "cosmic kids yoga": {
        "channel_name": "Cosmic Kids Yoga",
        "channel_url": "https://www.youtube.com/@CosmicKidsYoga",
        "image_url": "https://yt3.googleusercontent.com/Yc9p76OfTXkdYN5f0iGJqpfmgTZxZkmwvwmL6S7s63QA8UTuBFyBfjL6xYpsX-XdGiKqxfGWkQ=s240-c-k-c0x00ffffff-no-rj",
        "categories": ["kids", "family", "fitness"],
        "subscribers": "2M+",
        "description": "Kids yoga, mindfulness, and movement videos",
    },
    "ryan's world": {
        "channel_name": "Ryan's World",
        "channel_url": "https://www.youtube.com/@RyansWorld",
        "image_url": "https://yt3.googleusercontent.com/ytc/AIdro_mIPCAPZ4k1NbKEYcWQ-TbtucaftdvpIaBZRjzOodYoWGA=s240-c-k-c0x00ffffff-no-rj",
        "categories": ["kids", "family"],
        "subscribers": "37M+",
        "description": "Toy reviews, family adventures, and educational content for kids",
    },
    "diana and roma": {
        "channel_name": "Diana and Roma",
        "channel_url": "https://www.youtube.com/@DianaandRoma",
        "image_url": "https://yt3.googleusercontent.com/HQmL5wTUgzj9-oOZ0IfRidGZBgnqqKrljQ5LSi6cZVQNqzDQx3N0UeOEyHDUL6bWZkYdGUD6=s240-c-k-c0x00ffffff-no-rj",
        "categories": ["kids", "family"],
        "subscribers": "120M+",
        "description": "Family adventures and pretend-play with sibling duo",
    },
    "evantubehd": {
        "channel_name": "EvanTubeHD",
        "channel_url": "https://www.youtube.com/@EvanTube",
        "image_url": "https://yt3.googleusercontent.com/-ylDX9AYpkOO9ZniaPNgQoylONTvXm_AgmhTRsE6VgwrB_yHwh6EEQmV6AWLFtlKkQElgC_m_w=s240-c-k-c0x00ffffff-no-rj",
        "categories": ["kids", "family"],
        "subscribers": "6M+",
        "description": "Family vlogs, toy reviews, and kid-friendly entertainment",
    },
    "whatsupmoms": {
        "channel_name": "WhatsUpMoms",
        "channel_url": "https://www.youtube.com/@WhatsUpMoms",
        "image_url": "https://yt3.googleusercontent.com/ytc/AIdro_ms6sokR7UG1ZOXgQeULXeYN5B5qNOrWgEk2mdSqdqbvNU=s240-c-k-c0x00ffffff-no-rj",
        "categories": ["family", "lifestyle", "female-skewing"],
        "subscribers": "3M+",
        "description": "Parenting hacks, recipes, and lifestyle content for moms",
    },
    "guava juice": {
        "channel_name": "Guava Juice",
        "channel_url": "https://www.youtube.com/@GuavaJuice",
        "image_url": "https://yt3.googleusercontent.com/ytc/AIdro_lfI_Zm_EqpuQztoNH9Vdsw2YdRAgpbh-9cuqkBGruKxic=s240-c-k-c0x00ffffff-no-rj",
        "categories": ["family", "general-entertainment"],
        "subscribers": "18M+",
        "description": "DIY challenges, experiments, and family-friendly entertainment",
    },
    "the holderness family": {
        "channel_name": "The Holderness Family",
        "channel_url": "https://www.youtube.com/@TheHoldernessFamily",
        "image_url": "https://yt3.googleusercontent.com/J47zG3_oEBkMRnPuI0GM0AT-bxtsa74lN69ZN30IYuAUd9dTBkNgIMX-o01qaWDBPFPEjDQebw=s240-c-k-c0x00ffffff-no-rj",
        "categories": ["family", "general-entertainment", "lifestyle"],
        "subscribers": "1M+",
        "description": "Family parodies, songs, and relatable parenting moments",
    },
    "mrbeast": {
        "channel_name": "MrBeast",
        "channel_url": "https://www.youtube.com/@MrBeast",
        "image_url": "https://yt3.googleusercontent.com/nxYrc_1_2f77DoBadyxMTmv7ZpRZapHR5jbuYe7PlPd5cIRJxtNNEYyOC0ZsxaDyJJzXrnJiuDE=s240-c-k-c0x00ffffff-no-rj",
        "categories": ["general-entertainment", "family"],
        "subscribers": "330M+",
        "description": "Massive-scale challenges, philanthropy, and viral entertainment",
    },
    "dude perfect": {
        "channel_name": "Dude Perfect",
        "channel_url": "https://www.youtube.com/@DudePerfect",
        "image_url": "https://yt3.googleusercontent.com/nZRsCgyfOVFhBzY-YFV8AhdMcYAybNZ8uttjcsrUGOnGRSVF5yKqRh6XHIs_o03TcbixvlOZ=s240-c-k-c0x00ffffff-no-rj",
        "categories": ["sports", "general-entertainment", "family", "male-skewing"],
        "subscribers": "60M+",
        "description": "Trick shots, sports stunts, and family-friendly competitions",
    },
    "mark rober": {
        "channel_name": "Mark Rober",
        "channel_url": "https://www.youtube.com/@MarkRober",
        "image_url": "https://yt3.googleusercontent.com/ytc/AIdro_ksXY2REjZ6gYKSgnWT5jC_zT9mX900vyFtVinR8KbHww=s240-c-k-c0x00ffffff-no-rj",
        "categories": ["science", "general-entertainment", "family"],
        "subscribers": "67M+",
        "description": "Engineering, science experiments, and inventive builds",
    },
    "mkbhd": {
        "channel_name": "Marques Brownlee (MKBHD)",
        "channel_url": "https://www.youtube.com/@mkbhd",
        "image_url": "https://yt3.googleusercontent.com/qu4TmIaYUlS41-dJ9gZ7DUR3nilvmB5_11i6OKSdvNnBNiyOusZP1bMN6ICnuxtjFBb6ioKgRQ=s240-c-k-c0x00ffffff-no-rj",
        "categories": ["tech", "male-skewing"],
        "subscribers": "20M+",
        "description": "Premium consumer tech reviews and product breakdowns",
    },
    "fireship": {
        "channel_name": "Fireship",
        "channel_url": "https://www.youtube.com/@Fireship",
        "image_url": "https://yt3.googleusercontent.com/3fPNbkf_xPyCleq77ZhcxyeorY97NtMHVNUbaAON_RBDH9ydL4hJkjxC8x_4mpuopkB8oI7Ct6Y=s240-c-k-c0x00ffffff-no-rj",
        "categories": ["tech", "male-skewing"],
        "subscribers": "4M+",
        "description": "Software development, web tech, and developer-focused content",
    },
    "dr. dray": {
        "channel_name": "Dr. Dray",
        "channel_url": "https://www.youtube.com/@DrDray",
        "image_url": "https://yt3.googleusercontent.com/ytc/AIdro_l_BARhckRoCHj4IQDsV0j1iz4UiGjaMst5L6GG4OY=s240-c-k-c0x00ffffff-no-rj",
        "categories": ["beauty", "lifestyle", "female-skewing"],
        "subscribers": "1.5M+",
        "description": "Dermatologist-led skincare reviews and beauty science",
    },
    "hyram": {
        "channel_name": "Hyram",
        "channel_url": "https://www.youtube.com/@Hyram",
        "image_url": "https://yt3.googleusercontent.com/ytc/AIdro_lRVywRnN9XeTrQEJpg9-EZ2zHlLMrHqaiPeGbV_p0ILAk=s240-c-k-c0x00ffffff-no-rj",
        "categories": ["beauty", "lifestyle"],
        "subscribers": "5M+",
        "description": "Skincare expert reviewing routines, ingredients, and brands",
    },
    "pat mcafee": {
        "channel_name": "Pat McAfee",
        "channel_url": "https://www.youtube.com/@ThePMSShow",
        "image_url": "https://yt3.googleusercontent.com/ytc/AIdro_kqoMiE2Bf2cxY-AMuer4iGv4EuYzseTzUfjPR7f28=s240-c-k-c0x00ffffff-no-rj",
        "categories": ["sports", "general-entertainment", "male-skewing"],
        "subscribers": "4M+",
        "description": "Daily sports show with NFL coverage, hot takes, and interviews",
    },
    "lavendaire": {
        "channel_name": "Lavendaire",
        "channel_url": "https://www.youtube.com/@Lavendaire",
        "image_url": "https://yt3.googleusercontent.com/BV93psvV7-sWxPKcFRb7FlDEg2UEv9kDwDIOBppCE7Ri74uzAcn6O5lv3vidRTvfWOoklTR_h8M=s240-c-k-c0x00ffffff-no-rj",
        "categories": ["lifestyle", "female-skewing"],
        "subscribers": "700K+",
        "description": "Personal growth, productivity, and intentional living for young adults",
    },
    "storyline online": {
        "channel_name": "Storyline Online",
        "channel_url": "https://www.youtube.com/@StorylineOnline",
        "image_url": "https://yt3.googleusercontent.com/h11i0p5FnpjJ9RQAjNnrc_qi5Q8f3pbv2M685hyQjkobZZi3CenpaFVByZ6A-_d2ZZNUEnEh=s240-c-k-c0x00ffffff-no-rj",
        "categories": ["kids", "family"],
        "subscribers": "1M+",
        "description": "Celebrities reading children's books aloud",
    },
    "blippi": {
        "channel_name": "Blippi",
        "channel_url": "https://www.youtube.com/@Blippi",
        "image_url": "https://yt3.googleusercontent.com/t_0zKAbFUTLdh3JwAEahKAd-su7ZJ9T1jBkwdtKr24Wsq7MzxbWWjVRFH2D5WQQQ0GYn8i0MVQ=s240-c-k-c0x00ffffff-no-rj",
        "categories": ["kids", "family"],
        "subscribers": "20M+",
        "description": "Educational kids content with vehicles, places, and learning",
    },
    "cocomelon": {
        "channel_name": "Cocomelon",
        "channel_url": "https://www.youtube.com/@Cocomelon",
        "image_url": "https://yt3.googleusercontent.com/yiljI_XQcX8X0p_E2S0APGrUs7tHBMukf5_3dhVzhbH-z5uhzpt88tUopQa7ngVwO1nGAAnr6A=s240-c-k-c0x00ffffff-no-rj",
        "categories": ["kids", "family"],
        "subscribers": "190M+",
        "description": "Nursery rhymes, sing-alongs, and educational songs for toddlers",
    },

    # ── Sports / Male-skewing / Athletics ──
    "athlean-x": {
        "channel_name": "Athlean-X",
        "channel_url": "https://www.youtube.com/@athleanx",
        "image_url": "",
        "categories": ["fitness", "sports", "male-skewing"],
        "subscribers": "14M+",
        "description": "Training science, functional fitness, and workout programming",
    },
    "joe rogan": {
        "channel_name": "Joe Rogan Experience",
        "channel_url": "https://www.youtube.com/@joerogan",
        "image_url": "",
        "categories": ["general-entertainment", "sports", "male-skewing"],
        "subscribers": "19M+",
        "description": "Long-form conversations with athletes, comedians, and thinkers",
    },
    "barstool sports": {
        "channel_name": "Barstool Sports",
        "channel_url": "https://www.youtube.com/@barstoolsports",
        "image_url": "",
        "categories": ["sports", "general-entertainment", "male-skewing"],
        "subscribers": "3M+",
        "description": "Sports commentary, lifestyle, and viral pop-culture takes",
    },
    "first take": {
        "channel_name": "ESPN First Take",
        "channel_url": "https://www.youtube.com/@FirstTake",
        "image_url": "",
        "categories": ["sports", "general-entertainment", "male-skewing"],
        "subscribers": "3M+",
        "description": "Daily sports debate show covering NFL, NBA, MLB",
    },

    # ── Tech / Tools / Gear ──
    "linus tech tips": {
        "channel_name": "Linus Tech Tips",
        "channel_url": "https://www.youtube.com/@LinusTechTips",
        "image_url": "",
        "categories": ["tech", "male-skewing", "general-entertainment"],
        "subscribers": "16M+",
        "description": "PC building, hardware reviews, and consumer-tech deep dives",
    },
    "unbox therapy": {
        "channel_name": "Unbox Therapy",
        "channel_url": "https://www.youtube.com/@unboxtherapy",
        "image_url": "",
        "categories": ["tech", "general-entertainment", "male-skewing"],
        "subscribers": "25M+",
        "description": "Unboxings and first-impressions of gadgets, tools, and products",
    },
    "jerryrigeverything": {
        "channel_name": "JerryRigEverything",
        "channel_url": "https://www.youtube.com/@JerryRigEverything",
        "image_url": "",
        "categories": ["tech", "male-skewing"],
        "subscribers": "8M+",
        "description": "Teardown and durability tests for phones and consumer tech",
    },

    # ── Beauty / Skincare / Female-skewing ──
    "james charles": {
        "channel_name": "James Charles",
        "channel_url": "https://www.youtube.com/@jamescharles",
        "image_url": "",
        "categories": ["beauty", "lifestyle", "female-skewing"],
        "subscribers": "24M+",
        "description": "Makeup artistry, tutorials, and celebrity beauty collabs",
    },
    "nikkietutorials": {
        "channel_name": "NikkieTutorials",
        "channel_url": "https://www.youtube.com/@NikkieTutorials",
        "image_url": "",
        "categories": ["beauty", "lifestyle", "female-skewing"],
        "subscribers": "14M+",
        "description": "High-production makeup tutorials and trend breakdowns",
    },
    "safiya nygaard": {
        "channel_name": "Safiya Nygaard",
        "channel_url": "https://www.youtube.com/@SafiyaNygaard",
        "image_url": "",
        "categories": ["beauty", "lifestyle", "general-entertainment", "female-skewing"],
        "subscribers": "9M+",
        "description": "Beauty experiments, viral-product tests, and lifestyle investigations",
    },

    # ── Food / Cooking ──
    "babish culinary": {
        "channel_name": "Babish Culinary Universe",
        "channel_url": "https://www.youtube.com/@babishculinaryuniverse",
        "image_url": "",
        "categories": ["food", "general-entertainment"],
        "subscribers": "11M+",
        "description": "Recreating iconic dishes from movies, TV, and culture",
    },
    "joshua weissman": {
        "channel_name": "Joshua Weissman",
        "channel_url": "https://www.youtube.com/@JoshuaWeissman",
        "image_url": "",
        "categories": ["food", "general-entertainment", "male-skewing"],
        "subscribers": "10M+",
        "description": "Fast-food remakes, from-scratch cooking, and culinary experiments",
    },
    "bon appetit": {
        "channel_name": "Bon Appétit",
        "channel_url": "https://www.youtube.com/@bonappetit",
        "image_url": "",
        "categories": ["food", "lifestyle"],
        "subscribers": "6M+",
        "description": "Professional chef techniques, recipes, and cooking challenges",
    },

    # ── Fitness / Wellness ──
    "chloe ting": {
        "channel_name": "Chloe Ting",
        "channel_url": "https://www.youtube.com/@ChloeTing",
        "image_url": "",
        "categories": ["fitness", "lifestyle", "female-skewing"],
        "subscribers": "24M+",
        "description": "At-home workout programs, challenges, and fitness routines",
    },
    "yoga with adriene": {
        "channel_name": "Yoga With Adriene",
        "channel_url": "https://www.youtube.com/@yogawithadriene",
        "image_url": "",
        "categories": ["fitness", "lifestyle", "female-skewing"],
        "subscribers": "12M+",
        "description": "Accessible yoga, mindfulness, and breathwork routines",
    },

    # ── Lifestyle / Vlog / General ──
    "casey neistat": {
        "channel_name": "Casey Neistat",
        "channel_url": "https://www.youtube.com/@CaseyNeistat",
        "image_url": "",
        "categories": ["lifestyle", "general-entertainment", "male-skewing"],
        "subscribers": "13M+",
        "description": "Cinematic vlogs, filmmaking craft, and New York storytelling",
    },
    "yes theory": {
        "channel_name": "Yes Theory",
        "channel_url": "https://www.youtube.com/@yestheory",
        "image_url": "",
        "categories": ["lifestyle", "general-entertainment", "sports"],
        "subscribers": "9M+",
        "description": "Travel, adventure challenges, and comfort-zone storytelling",
    },
    "emma chamberlain": {
        "channel_name": "Emma Chamberlain",
        "channel_url": "https://www.youtube.com/@emmachamberlain",
        "image_url": "",
        "categories": ["lifestyle", "general-entertainment", "female-skewing"],
        "subscribers": "12M+",
        "description": "Gen-Z lifestyle, coffee, fashion, and relatable vlogs",
    },

    # ── Science / Education / General appeal ──
    "veritasium": {
        "channel_name": "Veritasium",
        "channel_url": "https://www.youtube.com/@veritasium",
        "image_url": "",
        "categories": ["science", "general-entertainment", "male-skewing"],
        "subscribers": "17M+",
        "description": "Physics, engineering, and science-of-everyday-life explainers",
    },
    "kurzgesagt": {
        "channel_name": "Kurzgesagt – In a Nutshell",
        "channel_url": "https://www.youtube.com/@kurzgesagt",
        "image_url": "",
        "categories": ["science", "general-entertainment"],
        "subscribers": "22M+",
        "description": "Animated deep-dives on science, space, biology, and big ideas",
    },

    # ── Home / Family / DIY ──
    "good mythical morning": {
        "channel_name": "Good Mythical Morning",
        "channel_url": "https://www.youtube.com/@goodmythicalmorning",
        "image_url": "",
        "categories": ["general-entertainment", "food", "family"],
        "subscribers": "19M+",
        "description": "Daily comedy talk show with food challenges and pop culture",
    },
    "bdylanhollis": {
        "channel_name": "B. Dylan Hollis",
        "channel_url": "https://www.youtube.com/@bdylanhollis",
        "image_url": "",
        "categories": ["food", "general-entertainment", "family"],
        "subscribers": "16M+",
        "description": "Vintage-recipe cooking with comedy and musical flair",
    },

    # ── Pets / Animals ──
    "tucker budzyn": {
        "channel_name": "Tucker Budzyn",
        "channel_url": "https://www.youtube.com/@tuckerbudzyn",
        "image_url": "",
        "categories": ["family", "lifestyle", "general-entertainment"],
        "subscribers": "4M+",
        "description": "Golden retriever lifestyle vlogs and narrated dog storytelling",
    },

    # ── Automotive / Tools / Male-skewing utility ──
    "donut": {
        "channel_name": "Donut Media",
        "channel_url": "https://www.youtube.com/@Donut",
        "image_url": "",
        "categories": ["general-entertainment", "tech", "male-skewing"],
        "subscribers": "6M+",
        "description": "Automotive culture, car storytelling, and industry breakdowns",
    },

    # ── Broad entertainment / Reaction / General ──
    "binging with babish": {
        "channel_name": "Binging With Babish",
        "channel_url": "https://www.youtube.com/@bingingwithbabish",
        "image_url": "",
        "categories": ["food", "general-entertainment", "male-skewing"],
        "subscribers": "10M+",
        "description": "Pop-culture recipes and culinary storytelling",
    },
    "zach king": {
        "channel_name": "Zach King",
        "channel_url": "https://www.youtube.com/@ZachKing",
        "image_url": "",
        "categories": ["general-entertainment", "family"],
        "subscribers": "31M+",
        "description": "Short-form visual-effects magic and viral comedy",
    },
    "first we feast": {
        "channel_name": "First We Feast",
        "channel_url": "https://www.youtube.com/@FirstWeFeast",
        "image_url": "",
        "categories": ["food", "general-entertainment"],
        "subscribers": "16M+",
        "description": "Hot Ones celebrity interviews and food culture deep-dives",
    },
}


# ---------------------------------------------------------------------------
# Brand industry → preferred channel categories (ranked best-first)
# ---------------------------------------------------------------------------

INDUSTRY_TO_CHANNEL_CATEGORIES: dict[str, list[str]] = {
    # Baby / kids products → kids and family channels
    "baby":        ["kids", "family"],
    "kids":        ["kids", "family"],
    "toddler":     ["kids", "family"],
    "toy":         ["kids", "family", "general-entertainment"],
    "nursery":     ["kids", "family"],

    # Beauty / personal care → beauty, lifestyle
    "beauty":      ["beauty", "lifestyle", "female-skewing", "general-entertainment"],
    "skincare":    ["beauty", "lifestyle", "female-skewing"],
    "cosmetic":    ["beauty", "lifestyle", "female-skewing"],
    "hair":        ["beauty", "lifestyle", "female-skewing"],
    "fragrance":   ["beauty", "lifestyle", "female-skewing"],
    "makeup":      ["beauty", "lifestyle", "female-skewing"],

    # Health / supplements / wellness → lifestyle, fitness, general
    "supplement":  ["lifestyle", "fitness", "general-entertainment"],
    "vitamin":     ["lifestyle", "fitness", "general-entertainment"],
    "wellness":    ["lifestyle", "fitness", "female-skewing"],
    "nutrition":   ["lifestyle", "fitness", "general-entertainment"],
    "health":      ["lifestyle", "fitness", "general-entertainment"],
    "probiotic":   ["lifestyle", "fitness", "general-entertainment"],
    "mental":      ["lifestyle", "general-entertainment"],

    # Fashion / apparel → lifestyle, beauty, general
    "fashion":     ["lifestyle", "beauty", "female-skewing", "general-entertainment"],
    "apparel":     ["lifestyle", "beauty", "general-entertainment"],
    "clothing":    ["lifestyle", "beauty", "general-entertainment"],
    "footwear":    ["sports", "lifestyle", "general-entertainment"],
    "shoe":        ["sports", "lifestyle", "general-entertainment"],
    "jewelry":     ["beauty", "lifestyle", "female-skewing"],
    "accessory":   ["lifestyle", "beauty", "female-skewing"],

    # Sports / fitness → sports, fitness, male-skewing
    "sport":       ["sports", "fitness", "male-skewing", "general-entertainment"],
    "athletic":    ["sports", "fitness", "general-entertainment"],
    "fitness":     ["fitness", "sports", "general-entertainment"],
    "outdoor":     ["sports", "general-entertainment", "family"],
    "gym":         ["fitness", "sports", "male-skewing"],

    # Food / beverage / candy / snacks → general-entertainment, family
    "food":        ["food", "general-entertainment", "family"],
    "beverage":    ["food", "general-entertainment", "family"],
    "candy":       ["general-entertainment", "family"],
    "sour":        ["general-entertainment", "family"],   # candy hint (e.g. finalbosssour)
    "sweet":       ["general-entertainment", "family"],
    "chocolate":   ["food", "general-entertainment", "family"],
    "snack":       ["general-entertainment", "family"],
    "drink":       ["food", "general-entertainment", "family"],
    "soda":        ["general-entertainment", "family"],
    "coffee":      ["food", "lifestyle", "general-entertainment"],
    "tea":         ["food", "lifestyle", "female-skewing"],
    "alcohol":     ["general-entertainment", "lifestyle", "male-skewing"],
    "wine":        ["food", "lifestyle"],
    "spirits":     ["general-entertainment", "lifestyle", "male-skewing"],

    # Pet → family, general-entertainment
    "pet":         ["family", "general-entertainment", "lifestyle"],
    "dog":         ["family", "general-entertainment", "lifestyle"],
    "cat":         ["family", "general-entertainment", "lifestyle"],

    # Home / furniture / decor → family, lifestyle
    "furniture":   ["family", "lifestyle", "general-entertainment"],
    "home":        ["family", "lifestyle", "general-entertainment"],
    "decor":       ["lifestyle", "family", "female-skewing"],
    "kitchen":     ["food", "lifestyle", "family"],
    "appliance":   ["family", "lifestyle", "general-entertainment"],
    "bedding":     ["family", "lifestyle", "female-skewing"],
    "garden":      ["family", "lifestyle", "general-entertainment"],

    # Tech / electronics / gaming
    "tech":        ["tech", "general-entertainment", "male-skewing"],
    "electronic":  ["tech", "general-entertainment", "male-skewing"],
    "gadget":      ["tech", "general-entertainment", "male-skewing"],
    "audio":       ["tech", "general-entertainment", "male-skewing"],
    "gaming":      ["general-entertainment", "tech", "male-skewing"],
    "computer":    ["tech", "general-entertainment", "male-skewing"],

    # Auto / tools → male-skewing general
    "auto":        ["general-entertainment", "tech", "male-skewing"],
    "automotive":  ["general-entertainment", "tech", "male-skewing"],
    "tool":        ["general-entertainment", "tech", "male-skewing"],

    # Gender / demographic hints often found in domain or brand name.
    # These keys get strict word-boundary matching (see _STRICT_BOUNDARY_KEYWORDS)
    # so "men" won't fire inside "women", "mom" won't fire inside "momentum", etc.
    "men":         ["sports", "general-entertainment", "male-skewing", "tech"],
    "man":         ["sports", "general-entertainment", "male-skewing"],
    "dad":         ["sports", "family", "general-entertainment", "male-skewing"],
    "father":      ["family", "sports", "male-skewing"],
    "women":       ["beauty", "lifestyle", "female-skewing"],
    "woman":       ["beauty", "lifestyle", "female-skewing"],
    "mom":         ["family", "lifestyle", "female-skewing"],
    "mother":      ["family", "lifestyle", "female-skewing"],
    "girl":        ["beauty", "lifestyle", "female-skewing"],

    # Travel / luggage / outdoor gear
    "travel":      ["lifestyle", "general-entertainment", "family"],
    "luggage":     ["lifestyle", "general-entertainment", "family"],
    "suitcase":    ["lifestyle", "general-entertainment", "family"],
    "bag":         ["lifestyle", "beauty", "general-entertainment"],
    "camp":        ["sports", "family", "general-entertainment"],
    "hiking":      ["sports", "family", "general-entertainment"],
    "adventure":   ["sports", "family", "general-entertainment"],

    # Grooming / shaving (male-skewing)
    "grooming":    ["lifestyle", "male-skewing", "general-entertainment"],
    "shave":       ["lifestyle", "male-skewing", "general-entertainment"],
    "beard":       ["lifestyle", "male-skewing", "general-entertainment"],

    # Menswear-specific cues (the compound form is a strong male signal)
    "menswear":    ["sports", "lifestyle", "male-skewing", "general-entertainment"],
    "mens":        ["sports", "lifestyle", "male-skewing"],
    "dude":        ["sports", "general-entertainment", "male-skewing", "lifestyle"],
    "bro":         ["sports", "general-entertainment", "male-skewing"],
    "guy":         ["sports", "general-entertainment", "male-skewing"],

    # Sleepwear / loungewear — GENDER-NEUTRAL by default.
    # A "robe" brand like wearecozyland.com is typically female-leaning
    # loungewear, not male. Let gender fall out of other signals in the
    # description (e.g. "for women", "women-founded") rather than baking
    # in a wrong default here.
    "robe":        ["lifestyle", "family", "general-entertainment"],
    "loungewear":  ["lifestyle", "general-entertainment", "family"],
    "underwear":   ["lifestyle", "general-entertainment", "family"],
    "pajama":      ["lifestyle", "family", "general-entertainment"],
    "sleepwear":   ["lifestyle", "family", "general-entertainment"],

    # Womenswear / women-leaning apparel cues (symmetric)
    "womenswear":  ["beauty", "lifestyle", "female-skewing"],
    "womens":      ["beauty", "lifestyle", "female-skewing"],
    "lady":        ["beauty", "lifestyle", "female-skewing"],
    "dress":       ["beauty", "lifestyle", "female-skewing"],
    "lingerie":    ["beauty", "lifestyle", "female-skewing"],

    # Office / B2B
    "office":      ["tech", "general-entertainment", "lifestyle"],
    "desk":        ["tech", "general-entertainment", "lifestyle"],
    "chair":       ["family", "lifestyle", "general-entertainment"],
}

# Default channel mix when no industry match (broad-appeal, mass-reach)
DEFAULT_CHANNEL_CATEGORIES = ["general-entertainment", "family", "lifestyle"]


def lookup_channel(name: str) -> dict | None:
    """Look up a channel by name (case-insensitive). Returns dict with image_url, channel_url, etc."""
    key = name.lower().strip()
    if key in YOUTUBE_CHANNEL_PROFILES:
        return YOUTUBE_CHANNEL_PROFILES[key]
    # Fuzzy: try partial match
    for k, v in YOUTUBE_CHANNEL_PROFILES.items():
        if key in k or k in key:
            return v
    return None


# ---------------------------------------------------------------------------
# Keyword matching helpers
# ---------------------------------------------------------------------------

# Gender-sensitive words that collide with other English words when matched as
# substrings — these require strict whole-word matching.
#   "men"   would match inside "women", "government"
#   "mom"   would match inside "momentum", "momma"
#   "man"   would match inside "manhattan", "mansion", "manual"
#   "bro"   would match inside "broad", "bronze", "broken"
#   "dad"   would match inside "dada"
# With re.search(r"\bword(s?)\b", text) none of these collide.
_STRICT_BOUNDARY_KEYWORDS: frozenset[str] = frozenset({
    "men", "man", "woman", "women", "mom", "dad", "bro", "guy",
    "girl", "lady", "dude", "mens", "womens", "male", "female",
})

# High-confidence phrase signals. These count double in gender arbitration
# because they are much harder to trigger by accident than bare keywords
# ("men's apparel" is a much stronger male signal than "men" appearing in
# a random position). Each entry is (regex, categories, gender-or-None).
_PHRASE_SIGNALS: list[tuple[str, list[str], str | None]] = [
    (r"\bmen['\u2019]?s\b",                 ["sports", "lifestyle", "male-skewing"],   "male"),
    (r"\bwomen['\u2019]?s\b",               ["beauty", "lifestyle", "female-skewing"], "female"),
    (r"\bfor\s+(?:men|guys|dudes|dads)\b",  ["sports", "lifestyle", "male-skewing"],   "male"),
    (r"\bfor\s+(?:women|ladies|girls|moms)\b", ["beauty", "lifestyle", "female-skewing"], "female"),
    (r"\bmade\s+for\s+men\b",               ["sports", "lifestyle", "male-skewing"],   "male"),
    (r"\bmade\s+for\s+women\b",             ["beauty", "lifestyle", "female-skewing"], "female"),
    (r"\b(?:women|woman|female)[\s-]*(?:owned|founded|led|run)\b",
                                            ["beauty", "lifestyle", "female-skewing"], "female"),
    (r"\b(?:male|men)[\s-]*(?:focused|targeted)\b",
                                            ["sports", "lifestyle", "male-skewing"],   "male"),
]

# Unisex / gender-neutral signals. When any of these fires, we force a
# neutral outcome regardless of other keywords — "clothing for men and
# women" should not be biased toward either side just because "for men"
# happened to appear syntactically earlier.
_UNISEX_PHRASES: list[str] = [
    r"\bunisex\b",
    r"\bgender[\s-]*neutral\b",
    r"\bfor\s+everyone\b",
    r"\bfor\s+all\s+genders\b",
    r"\bfor\s+(?:men|guys|dudes)\s+and\s+(?:women|ladies|girls)\b",
    r"\bfor\s+(?:women|ladies|girls)\s+and\s+(?:men|guys|dudes)\b",
    r"\b(?:men|guys|dudes)\s+and\s+(?:women|ladies|girls)\b",
    r"\b(?:women|ladies|girls)\s+and\s+(?:men|guys|dudes)\b",
]


def _keyword_matches(keyword: str, text: str) -> bool:
    """Check if `keyword` appears in `text` using the right boundary rule.

    Strict keywords (short gender words that collide with other words) must
    match as a whole word, optionally with a plural "s". Everything else
    uses a leading word boundary only, so "toy" matches "toys", "beauty"
    matches "beautyful" (harmless), "sport" matches "sportswear", etc.
    """
    kw = keyword.strip()
    if not kw:
        return False
    if kw in _STRICT_BOUNDARY_KEYWORDS:
        return bool(re.search(r"\b" + re.escape(kw) + r"s?\b", text))
    return bool(re.search(r"\b" + re.escape(kw), text))


def _resolve_categories(industry: str | None, description: str | None) -> list[str]:
    """Given a brand industry/description, return ranked channel categories.

    Three-tier signal model:
      1. Phrase signals (e.g. "women-owned", "men's apparel") — high confidence,
         count as +2 gender weight.
      2. Keyword signals from INDUSTRY_TO_CHANNEL_CATEGORIES with word-boundary
         matching — +1 gender weight for gendered buckets.
      3. Gender arbitration — if both male and female signals fire, keep only
         the stronger one (≥2× the other), else drop both and go neutral.

    This prevents:
      - "men" matching inside "women" (and vice versa)
      - "robe" matching inside "wardrobe"
      - A unisex brand being pushed into male-only or female-only channels
      - Loungewear brands like wearecozyland.com from being flagged male-skewing
    """
    text = " ".join(filter(None, [industry, description])).lower()
    if not text:
        return DEFAULT_CHANNEL_CATEGORIES.copy()

    ranked: list[str] = []
    male_strength = 0
    female_strength = 0

    # Tier 1 — phrase signals (strongest, +2 each)
    for pattern, cats, gender in _PHRASE_SIGNALS:
        if re.search(pattern, text):
            for c in cats:
                if c not in ranked:
                    ranked.append(c)
            if gender == "male":
                male_strength += 2
            elif gender == "female":
                female_strength += 2

    # Tier 2 — keyword signals (+1 each, with boundary-aware matching)
    for keyword, cats in INDUSTRY_TO_CHANNEL_CATEGORIES.items():
        if _keyword_matches(keyword, text):
            for c in cats:
                if c not in ranked:
                    ranked.append(c)
            if "male-skewing" in cats:
                male_strength += 1
            if "female-skewing" in cats:
                female_strength += 1

    # Explicit unisex override — force neutral regardless of other signals
    unisex = any(re.search(p, text) for p in _UNISEX_PHRASES)
    if unisex:
        male_strength = 0
        female_strength = 0
        ranked = [c for c in ranked if c not in ("male-skewing", "female-skewing")]

    # Tier 3 — gender arbitration. If both signals fired, keep only the
    # dominant side (≥2× the other); otherwise drop both and stay neutral.
    if male_strength > 0 and female_strength > 0:
        if male_strength >= female_strength * 2:
            ranked = [c for c in ranked if c != "female-skewing"]
        elif female_strength >= male_strength * 2:
            ranked = [c for c in ranked if c != "male-skewing"]
        else:
            ranked = [c for c in ranked if c not in ("male-skewing", "female-skewing")]

    # Safety net: always include default broad-appeal categories as fallback
    for c in DEFAULT_CHANNEL_CATEGORIES:
        if c not in ranked:
            ranked.append(c)
    return ranked


def select_channels_for_brand(
    industry: str | None = None,
    description: str | None = None,
    n: int = 8,
) -> list[dict]:
    """Pick `n` YouTube channels aligned with the brand's industry / description.

    Returns list of dicts shaped for `_build_recommended_yt_channels` consumption:
      {name, channel_url, image_url, categories, subscribers, description, category_label}

    Channels are ranked by category match: a channel scores +1 for each of its
    categories that appears in the brand's resolved category list, weighted by
    that category's rank position (earlier = higher weight). Ties broken by
    subscriber size (rough proxy via parsing the leading number).
    """
    ranked_cats = _resolve_categories(industry, description)
    cat_weight = {c: (len(ranked_cats) - i) for i, c in enumerate(ranked_cats)}

    # When the brand clearly isn't kid-targeted, skip channels whose PRIMARY
    # audience is kids — otherwise Cocomelon/Ms Rachel get pulled into the
    # overflow for menswear, supplements, finance, etc. A brand is considered
    # kid-adjacent only if "kids" is in its top category list.
    kids_ok = "kids" in ranked_cats

    def _subs_score(s: str) -> float:
        """Crude parse: '200M+' → 200, '1.5M+' → 1.5, '700K+' → 0.7."""
        if not s:
            return 0
        try:
            num_part = "".join(ch for ch in s if ch.isdigit() or ch == ".")
            val = float(num_part) if num_part else 0
            if "M" in s.upper():
                return val
            if "K" in s.upper():
                return val / 1000
            return val
        except (ValueError, TypeError):
            return 0

    scored = []
    unscored = []
    for key, prof in YOUTUBE_CHANNEL_PROFILES.items():
        cats = prof.get("categories", [])
        # Hard filter: drop kids-primary channels for adult brands
        if not kids_ok and "kids" in cats:
            continue
        match_score = sum(cat_weight.get(c, 0) for c in cats)
        subs = _subs_score(prof.get("subscribers", ""))
        if match_score > 0:
            scored.append((match_score, subs, key, prof))
        else:
            # Still eligible to pad the list when the scored set is < n,
            # sorted purely by subscriber size.
            unscored.append((0, subs, key, prof))

    # Sort scored by match score desc, then subscribers desc;
    # unscored by subscribers desc as the fallback tier.
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    unscored.sort(key=lambda t: t[1], reverse=True)

    # Guarantee the caller always gets `n` channels whenever the pool
    # supports it — pad with the biggest remaining (non-kids-for-adult-brand)
    # channels when fewer than `n` have positive category overlap.
    combined = scored + unscored
    picked = combined[:n]

    # Build result with friendly category label (first matching cat)
    out = []
    for _score, _subs, _key, prof in picked:
        # Pick the first category that's in the brand's ranked list as the label
        label = next(
            (c for c in prof.get("categories", []) if c in ranked_cats),
            (prof.get("categories") or ["General"])[0],
        )
        out.append({
            "name": prof["channel_name"],
            "channel_url": prof["channel_url"],
            "image_url": prof.get("image_url", ""),
            "categories": prof.get("categories", []),
            "subscribers": prof.get("subscribers", ""),
            "description": prof.get("description", ""),
            "category_label": _format_category_label(label),
        })
    return out


def _format_category_label(category: str) -> str:
    """Convert internal category key → display label."""
    return {
        "kids": "Kids & Family",
        "family": "Family",
        "general-entertainment": "Entertainment",
        "sports": "Sports",
        "tech": "Tech & Reviews",
        "beauty": "Beauty & Skincare",
        "lifestyle": "Lifestyle",
        "food": "Food & Cooking",
        "fitness": "Fitness & Health",
        "science": "Science & Education",
        "female-skewing": "Lifestyle (Female)",
        "male-skewing": "Entertainment (Male)",
    }.get(category, category.title())
