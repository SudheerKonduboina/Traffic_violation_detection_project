from ultralytics import YOLO

def train_traffic():
    model = YOLO("yolov8n.pt")
    
    model.train(
        data="datasets/traffic/traffic.yaml",
        epochs=60,
        imgsz=640,
        batch=16,
        name="traffic_model"
    )

    model.export(format="pt")

if __name__ == "__main__":
    train_traffic()
