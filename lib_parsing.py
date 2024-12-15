import os
import requests
import urllib3
import bs4
from pathvalidate import sanitize_filename
from urllib.parse import urlsplit, urljoin
import argparse


def check_for_redirect(response: requests.Response) -> None:
    if response.history:
        raise requests.HTTPError("Book not found")
    return


def download_txt(
    url: str,
    textname: str = "Noname",
    folder: str = "books/"
) -> str:
    sanitized_filename = sanitize_filename(textname)
    response = requests.get(url, timeout=10, verify=False)
    text_path = os.path.join(folder, sanitized_filename)
    with open(f"{text_path}.txt", "w", encoding="utf-8") as file:
        file.write(response.text)
    return text_path


def download_img(url: str, folder: str = "images/") -> None:
    url_path = urlsplit(url).path
    img_name = url_path.split("/")[-1]
    response = requests.get(url, timeout=10, verify=False)
    img_path = os.path.join(folder, img_name)
    with open(img_path, "wb") as file:
        file.write(response.content)
    return img_path


def parse_book_page(mainpage_url: str, response: requests.Response) -> dict:
    soup = bs4.BeautifulSoup(response.text, "lxml")

    header_tag = soup.find("div", id="content").find("h1")
    author_tag = header_tag.find("a")
    image_tag = soup.find("div", class_="bookimage").find("a").find("img")
    texts_tags = soup.find_all("div", class_="texts")
    genre_tags = soup.find("span", class_="d_book").find_all("a")

    author = author_tag.text.strip()

    header_text = header_tag.text
    split_text = header_text.split("\xa0")

    book = split_text[0].strip()

    cover_url = urljoin(mainpage_url, image_tag["src"])

    comments = []
    for text_tag in texts_tags:
        comments.append(text_tag.find("span").text)

    genres = []
    for genre_tag in genre_tags:
        genres.append(genre_tag.text)

    return {
        "name": book,
        "author": author,
        "cover_url": cover_url,
        "comments": comments,
        "genres": genres,
    }


def get_book_page_response(
    mainpage_url: str,
    book_id: str
) -> requests.Response:
    book_url = f"{mainpage_url}/b{book_id}"
    response = requests.get(book_url, timeout=10, verify=False)
    response.raise_for_status()
    return response


def get_book_txt_response(
    mainpage_url: str,
    book_id: str
) -> requests.Response:
    url_template = f"{mainpage_url}/txt.php"
    params = {"id": book_id}
    response = requests.get(url_template, params=params,
                            timeout=10, verify=False)
    response.raise_for_status()
    return response


def download_books(start_id, end_id) -> dict:
    books_folder = "books/"
    covers_folder = "covers/"
    mainpage_url = "https://tululu.org"
    os.makedirs(books_folder, exist_ok=True)
    os.makedirs(covers_folder, exist_ok=True)
    books_downloaded = {}
    for book_id in range(start_id, end_id + 1):
        book_txt_response = get_book_txt_response(mainpage_url, book_id)
        try:
            check_for_redirect(book_txt_response)
        except requests.HTTPError:
            print("Book not found")
            print("----------------")
            continue

        book_page_response = get_book_page_response(mainpage_url, book_id)
        book_info = parse_book_page(mainpage_url, book_page_response)
        book = book_info["name"]
        author = book_info["author"]

        book_url = book_txt_response.url
        cover_url = book_info["cover_url"]
        filename = f"{book_id}. {book}. {author}"

        book_info["local_book_path"] = download_txt(
            book_url, filename, books_folder)
        book_info["local_cover_path"] = download_img(cover_url, covers_folder)

        books_downloaded[book_id] = book_info
        print(f"Название: {book}")
        print(f"Автор: {author}")
        print("----------------")
    return books_downloaded


def main():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    parser = argparse.ArgumentParser(
        description="Скачивание книг с tululu.org")
    parser.add_argument("--start_id", help="Начальный id", type=int, default=1)
    parser.add_argument("--end_id", help="Конечный id", type=int)
    args = parser.parse_args()
    start_id = args.start_id
    end_id = args.end_id
    if not end_id or end_id < start_id:
        end_id = start_id
    download_books(start_id, end_id)


if __name__ == "__main__":
    main()
