from ultralytics import YOLO

def train_plate():
    model = YOLO("yolov8n.pt")

    model.train(
        data="datasets/plate/plate.yaml",
        epochs=70,
        imgsz=640,
        batch=16,
        name="plate_model"
    )

    model.export(format="pt")

if __name__ == "__main__":
    train_plate()
