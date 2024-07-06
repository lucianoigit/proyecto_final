import torch
from app.abstracts.IMLModel import MLModelInterface

class MLModelService(MLModelInterface):
    def __init__(self, model_path: str, ):
        self.model_path = model_path
        self.model = self.load_model()


    def load_model(self):
        try:
            # Cargar el modelo personalizado de YOLOv5
            model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
            return model
        except Exception as e:
            print(f"Error al cargar el modelo: {e}")
            return None

    def run_model(self, img, confianza_minima=0.2):
        try:
            resultados = self.model(img)
            df = resultados.pandas().xyxy[0]
            df_filtrado = df[df['confidence'] >= confianza_minima]
            return df_filtrado, resultados # Esto devuelve el dataframe filtrado y la imagen con las detecciones dibujadas
        except Exception as e:
            print(f"Error al ejecutar el modelo: {e}")
            return None, None
        

    def show_result(self, result:any):
        if result is not None:
            result.show()
        else:
            print("No hay resultados para mostrar.")