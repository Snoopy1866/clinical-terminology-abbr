import json


class Content:
    def __init__(self, full_name: str, description: str) -> None:
        self.full_name = full_name.strip()
        self.description = description.strip()

    def __repr__(self) -> str:
        return f"Content({self.full_name}, {self.description})"


class Abbr:
    def __init__(self, name: str, content: Content | list[Content]) -> None:
        self.name = name.strip()
        self.content = content

    def __repr__(self) -> str:
        return f"Abbr({self.name}, {self.content})"


# 自定义 JSON 反序列化
class AbbrDecoder(json.JSONDecoder):
    def decode(self, s: str) -> Abbr:
        data = super().decode(s)
        abbr_list = []
        for abbr in data:
            content_data = abbr["content"]
            if isinstance(content_data, dict):
                content = Content(
                    content_data["full_name"], content_data["description"]
                )
            elif isinstance(content_data, list):
                content = [
                    Content(c["full_name"], c["description"]) for c in content_data
                ]
            else:
                raise ValueError("Invalid content data")
            abbr_list.append(Abbr(abbr["name"], content))
        return abbr_list


# 自定义 JSON 序列化
class AbbrEncoder(json.JSONEncoder):
    def default(self, obj: Abbr | Content) -> dict:
        if isinstance(obj, Abbr):
            return {"name": obj.name, "content": obj.content}
        if isinstance(obj, Content):
            return {"full_name": obj.full_name, "description": obj.description}
        else:
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def json2md(abbr_list: list[Abbr]) -> str:
    md = "# 缩写词表\n"
    md += "| 缩略语 | 全拼 | 释义 |\n"
    md += "| --- | --- | --- |\n"

    for abbr in abbr_list:
        if isinstance(abbr.content, Content):
            md += f"| {abbr.name} | {abbr.content.full_name} | {abbr.content.description} |\n"
        else:
            md += f"| {abbr.name} | {abbr.content[0].full_name} | {abbr.content[0].description} |\n"
            for sub_content in abbr.content[1:]:
                md += f"| | {sub_content.full_name} | {sub_content.description} |\n"

    return md


def title_case(name: str) -> str:
    # 一些特殊的缩写词应该保留原样
    exceptions = ["CT", "Isoenzymes-MB", "MRI", "Organ-at-Risk", "WHO"]
    # 助词、连词、介词、冠词、代词应该保持小写
    exceptions += [
        "a",
        "an",
        "the",
        "and",
        "or",
        "for",
        "at",
        "for",
        "in",
        "of",
        "on",
        "to",
        "with",
    ]

    words = name.split()
    title_cased_words = [word if word in exceptions else word.title() for word in words]
    return " ".join(title_cased_words)


# 检查是否有重复的缩写词
def check_duplicate(abbr_list: list[Abbr]) -> None:
    abbr_name_list = [abbr.name for abbr in abbr_list]
    duplicates = set(
        [name for name in abbr_name_list if abbr_name_list.count(name) > 1]
    )
    if duplicates:
        raise ValueError(f"Duplicate abbreviation names found: {', '.join(duplicates)}")


if __name__ == "__main__":
    # 读取 json 文件
    with open("abbr.json", "r+", encoding="utf-8") as f:
        abbr_list: list[Abbr] = json.load(f, cls=AbbrDecoder)

    # 检查重复缩写词
    check_duplicate(abbr_list)

    # 排序
    for abbr in abbr_list:
        if isinstance(abbr.content, list):
            abbr.content.sort(key=lambda x: x.full_name.lower())
    abbr_list.sort(key=lambda x: x.name.lower())

    # 大写转换
    for abbr in abbr_list:
        if isinstance(abbr.content, Content):
            abbr.content.full_name = title_case(abbr.content.full_name)
        else:
            for content in abbr.content:
                content.full_name = title_case(content.full_name)

    # 回写 json 文件
    with open("abbr.json", "w+", encoding="utf-8") as f:
        json.dump(abbr_list, f, cls=AbbrEncoder, ensure_ascii=False, indent=2)

    # 输出 markdown 文件
    with open("abbr.md", "w+", encoding="utf-8") as f:
        f.write(json2md(abbr_list))
