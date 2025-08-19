import requests
import os

def download_file(url, folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    local_filename = os.path.join(folder_name, url.split('/')[-1])
    print(f"Downloading {url} to {local_filename}")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return local_filename

# URLs for the datasets
cic_ids_2017_url = "http://205.174.165.80/CICDataset/CIC-IDS-2017/Dataset/MachineLearningCSV.zip"
cert_insider_threat_url = "https://kilthub.cmu.edu/ndownloader/files/12841247"


print("Downloading CIC-IDS 2017 dataset...")
download_file(cic_ids_2017_url, "data/raw")
print("CIC-IDS 2017 dataset downloaded successfully.")

print("Downloading CERT Insider Threat dataset...")
download_file(cert_insider_threat_url, "data/raw")
print("CERT Insider Threat dataset downloaded successfully.")