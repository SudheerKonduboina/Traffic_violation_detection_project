from ultralytics import YOLO

def train_helmet():
    model = YOLO("yolov8n.pt")  # start from pretrained COCO
    
    model.train(
        data="datasets/helmet/helmet.yaml",
        epochs=50,
        imgsz=640,
        batch=16,
        name="helmet_model"
    )

    model.export(format="pt")

if __name__ == "__main__":
    train_helmet()
