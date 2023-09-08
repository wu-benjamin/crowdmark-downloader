import time

from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import urllib.request
import html


def main():
    driver = webdriver.Chrome()
    driver.get("https://app.crowdmark.com/sign-in/waterloo")

    input("Press Enter after logging in: ")

    assert "Crowdmark" in driver.title
    working_directory = os.getcwd()

    output_directory = os.path.join(working_directory, "output")
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    start_time = time.time()
    download_assessments_for_ith_page(driver, output_directory, 1)
    end_time = time.time()

    elapsed_time = end_time - start_time
    print("Finished downloading in: ", elapsed_time, " seconds!")
    driver.close()
    exit(0)


def download_assessments_for_ith_page(driver, output_directory, starting_page):
    page_num = starting_page
    # for each page in crowdmark, install each assessment
    while True:
        # driver.get(f"https://app.crowdmark.com/student/courses?page={page_num}")
        driver.get(f"https://app.crowdmark.com/student/course-archive?page={page_num}")
        time.sleep(2)  # wait for page to load. For some reason driver.get doesn't wait for the entire page to load

        course_list = driver.find_element(By.CLASS_NAME, "student-dashboard__course-list")

        a_tags = course_list.find_elements(By.TAG_NAME, "a")

        if len(a_tags) == 0:
            # there are no more links on this page, so we have scraped all the assessments
            return

        urls = [a_tag.get_attribute("href") for a_tag in a_tags]
        for url in urls:
            download_assessments_for_course(driver, output_directory, url)

        page_num += 1


def download_assessments_for_course(driver, output_directory, url):
    course_name = page_name(url)
    driver.get(url)
    time.sleep(2)  # wait for page to load. For some reason driver.get doesn't wait for the entire page to load

    course_output_directory = os.path.join(output_directory, course_name)
    if not os.path.exists(course_output_directory):
        os.makedirs(course_output_directory)

    a_tags = driver.find_elements(By.TAG_NAME, "a")
    urls = [a_tag.get_attribute("href") for a_tag in a_tags]
    for assessment_url in urls:
        if (not assessment_url) or ("assessments" not in assessment_url):
            # this link doesn't take you to an assessment
            continue
        download_assessment(driver, course_output_directory, assessment_url)


def download_assessment(driver, course_output_directory, url):
    driver.get(url)
    time.sleep(2)  # wait for page to load. For some reason driver.get doesn't wait for the entire page to load
    assessment_name = page_name(url)

    assessment_output_directory = os.path.join(course_output_directory, assessment_name)
    if not os.path.exists(assessment_output_directory):
        os.makedirs(assessment_output_directory)

    external_local_file_name_map = {}

    images = driver.find_elements(By.TAG_NAME, "img")
    for i, image in enumerate(images):
        try:
            image_src = image.get_attribute('src')
            image_file_name = f"image_{i}.png"
            image_file_path = f"{assessment_output_directory}/{image_file_name}"
            driver.execute_script(f"arguments[0].removeAttribute('crossorigin');", image)
            urllib.request.urlretrieve(image_src, image_file_path)
            external_local_file_name_map[image_src] = image_file_name
        except:
            pass  # ignore alert

    buttons = driver.find_elements(By.CSS_SELECTOR, "ul button")
    for button in buttons:
        button.click()
        time.sleep(0.25)
        graph_file_name = f"{assessment_output_directory}/{button.get_attribute('innerHTML')}.png"
        graph = driver.find_elements(By.CSS_SELECTOR, ".score-distribution__chart");
        graph = graph[0]
        graph_png = graph.screenshot_as_png
        with open(graph_file_name, "wb") as graph_file:
            graph_file.write(graph_png)

    with open(f"{assessment_output_directory}/index.html", "w", encoding="utf-8") as file:
        html_page_source = driver.page_source
        for original_file_name in external_local_file_name_map:
            html_page_source = html_page_source.replace(html.escape(original_file_name), external_local_file_name_map[original_file_name])
        file.write(html_page_source)


def page_name(url):
    return url.rsplit('/', 1)[-1]


if __name__ == '__main__':
    main()
