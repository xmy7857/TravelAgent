name: weather_query
description: 查询某城市未来几天的天气情况
---
# Step1
调用maps_weather, 利用城市名称来查询未来几天的天气情况

# Step2
以如下形式返回结果：
```json
{
    "city": "城市名称"
    "weather": [
        {
            "date": "日期,如2026-05-02",
            "condition": "天气状况，如晴、小雨",
            "max_temperature": "最高温度",
            "min_temperature": "最低温度",
            "风力": "如东南风1-2级"
            "advice": "出行和穿衣建议"
        },
        {
            "date": "日期,如2026-05-02",
            "condition": "天气状况，如晴、小雨",
            "max_temperature": "最高温度",
            "min_temperature": "最低温度",
            "风力": "如东南风1-2级"
            "advice": "出行和穿衣建议"
        },
        ...
    ]
}
```

