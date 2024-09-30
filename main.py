import requests
import random
import time
import os.path
import json
from bs4 import BeautifulSoup
from random import randint

from PIL import Image
from urllib.parse import urlparse


main_url = "https://www.worthepenny.com/hand-test-proof/"  # main url to crawl but yet able to click load more automatically (403 Forbidden)


def get_soup(url):
    html = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36",
            "Referer": "https://www.google.com",
        },
    )
    soup = BeautifulSoup(html.content, "html.parser")
    return soup


def remove_duplicates():

    old_stores_list_json = None
    with open("stores-list-storage.json", "r") as f:
        old_stores_list_json = json.load(f)
        f.close()

    list1 = old_stores_list_json  # old store list
    list2 = get_info()  # get new store list

    print(
        "---------------------------------- Start Comparing And Downloading Images... ----------------------------------"
    )

    def find_unique_by_image(list1, list2):
        # Create a set of images in list1
        images_in_list1 = {item["image_paths_to_download"] for item in list1}

        # Find items in list2 whose images are not in list1
        unique_items = [
            item
            for item in list2
            if item["image_paths_to_download"] not in images_in_list1
        ]

        return unique_items

    # Find items in list2 that are not in list1 based on the images
    find_unique_by_image = find_unique_by_image(list1, list2)

    # check if there are new links
    if len(find_unique_by_image) > 0:
        # Write new items in old_stores_list_json file
        for store in find_unique_by_image:
            store = download_image(store, old_stores_list_json)
            old_stores_list_json.append(store)

        with open("stores-list-storage.json", "w") as file:
            json.dump(old_stores_list_json, file)
            file.close()

        print(
            f"-------------- Found {len(find_unique_by_image)} new image(s) ---------------"
        )
        return find_unique_by_image
    else:
        print(f"-------------- Not found any new image ---------------")
        return None


def download_image(store, stores_array):
    store = store

    # This to find how many stores already in the store array -> get the right index for the image
    duplicate_items = [
        item for item in stores_array if item["store_alias"] == store["store_alias"]
    ]
    count_duplicate_items = len(duplicate_items)

    folder_path = "images"
    try:
        # Send a GET request to the URL
        response = requests.get(store["image_paths_to_download"])

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Extract the file name from the URL
            parsed_url = urlparse(store["image_paths_to_download"])
            file_name = os.path.basename(parsed_url.path)

            # Extract the file extension
            file_extension = os.path.splitext(file_name)[1]

            image_index = count_duplicate_items + 1
            file_name_save_to_folder = f"hand-test-proof---{store['store_alias']}---code--{store['code']}---{image_index}"

            # Combine folder path and file name to create the full path
            file_path = os.path.join(
                folder_path, file_name_save_to_folder + file_extension
            )

            # Write the content of the response to a file
            with open(file_path, "wb") as f:
                f.write(response.content)

            print(f"Image downloaded successfully: {file_name_save_to_folder}")

            store["image_paths"] = file_name_save_to_folder
            return store
    except:
        if os.path.exists("errors.txt"):
            with open("errors.txt", "a") as link_error_file:
                link_error_file.write(store["image_paths_to_download"] + "\n")
        link_error_file.close()

        print("Error IMAGE url is ---> " + store["image_paths_to_download"])
        pass


def get_info():
    print(f"-------------- Start crawling new store info ---------------")
    all_stores_info = []

    page = 1
    while True:
        try:
            print(f"Current page is -------> {page}")
            paginators = f"https://www.worthepenny.com/api/get_hand_test_proof_coupons?page={page}"
            response = get_soup(paginators)

            div_element = response.find("div") if response.find("div") else None

            # If the current api dont have any data, break the script
            if div_element == None:
                print(f"No data found on page {page}. Stopping...")
                break

            # Find all store boxes on current page
            all_store_boxes = response.find_all("div", class_="glide__slide")

            # Check len
            if len(all_store_boxes) == 0:
                print(f"No data found on page {page}. Stopping...")
                break

            for store in all_store_boxes:

                info = {
                    "store_alias": (
                        store.find("a", class_="p_top worthepennycom")["href"]
                        .split("//")[1]
                        .split(".")[0]
                        if store.find("a", class_="p_top worthepennycom")["href"]
                        else ""
                    ),
                    "image_paths_to_download": (
                        store.find(
                            "div", class_="_img_box p_image worthepennycom"
                        ).find("img", class_="lazyload worthepennycom")["data-src"]
                        if store.find(
                            "div", class_="_img_box p_image worthepennycom"
                        ).find("img", class_="lazyload worthepennycom")["data-src"]
                        else ""
                    ),
                    "discount_percent": (
                        store.find("div", class_="p_text worthepennycom")
                        .find_all("p", class_="worthepennycom")[0]
                        .find("span")
                        .text.strip()
                        if store.find("div", class_="p_text worthepennycom").find_all(
                            "p", class_="worthepennycom"
                        )[0]
                        else "SALE"
                    ),
                    "code": (
                        store.find("div", class_="p_text worthepennycom")
                        .find_all("p", class_="worthepennycom")[1]
                        .text.strip()
                        .split("Code: ")[1]
                        if store.find("div", class_="p_text worthepennycom").find_all(
                            "p", class_="worthepennycom"
                        )[1]
                        else ""
                    ),
                    "link_store_details": (
                        store.find("a", class_="p_top worthepennycom")["href"]
                        if store.find("a", class_="p_top worthepennycom")["href"]
                        else ""
                    ),
                }

                all_stores_info.append(info)

            page += 1
            time.sleep(random.randint(1, 3))

        except:
            if os.path.exists("errors.txt"):
                with open("errors.txt", "a") as link_error_file:
                    link_error_file.write(paginators + "\n")
            link_error_file.close()

            print("Error url is: " + paginators)
            break

    return all_stores_info


############################################ EXECUTE FUNCTIONS HERE ####################################################
#####---> How does this script work?
#####---> 1. Get stores-list-storage data, crawl new store, compares if the two arrays have new store(s), based on 'image_paths_to_download', aka 'image source'
#####--------> - If it has new store, download the image then append to existing store array
#####--------> - Else print out 'Not found any new image(s)'
#####---> 2. Logic crawling data:
#####--------> Crawls all page pagination data, if the current page has no div element, break the loop
#####---> 3. Variable time_sleep controls how long script runs again


def main():
    remove_duplicates()


""" sleep for 24 hours """
# time_sleep = 86400
# while True:
#     main()
#     time.sleep(time_sleep)

""" run once """
main()
