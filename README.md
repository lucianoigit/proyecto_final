# Proyecto Final: Sistema de Clasificación Automática de Objetos

Este proyecto implementa un sistema completo de clasificación automática de objetos utilizando el modelo de detección YOLOv11, integración con cámaras Raspberry Pi, y un sistema de transporte controlado por un ESP32. El sistema permite identificar, clasificar y gestionar objetos dentro de un área de trabajo predefinida, con capacidades de configuración avanzadas a través de una interfaz HMI.

## Características Principales

- **Clasificación en Tiempo Real**: Basado en YOLOv11 para detección precisa y rápida.
- **Interfaz HMI Personalizable**: Configura clases, coordenadas, velocidad de transporte y área de trabajo.
- **Gestor de Cámara**: Captura de imágenes con corrección de distorsión.
- **Detección y Análisis**: Identifica objetos dentro de un área de trabajo y proporciona estadísticas detalladas.
- **Control Integrado**: Comunicación directa con ESP32 para gestión del transporte de objetos.

## Requisitos Previos

### Hardware
- Raspberry Pi 3 B o superior.
- Cámara compatible con Raspberry Pi (Picamera2).
- ESP32 para control del sistema de transporte.

### Software
- Python 3.9.2 (Raspberry Pi).
- Dependencias Python (ver sección "Instalación").
- Modelo YOLOv11 preentrenado.

### Librerías Utilizadas

- `opencv-python`
- `ultralytics` (para YOLO)
- `numpy`
- `pandas`
- `customtkinter` (para HMI)
- `picamera2`

## Instalación

1. **Clona el Repositorio**:
   ```bash
   git clone <URL-del-repositorio>
   cd <directorio-del-proyecto>
   ```

2. **Crea un Entorno Virtual**:
   ```bash
   python3 -m venv env
   source env/bin/activate
   ```

3. **Instala las Dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configura el Modelo YOLO**:
   - Descarga el modelo YOLOv11 preentrenado y colócalo en el directorio `models/`.

5. **Configura el Sistema**:
   - Asegúrate de que las conexiones entre la Raspberry Pi y el ESP32 estén correctamente configuradas.

## Uso

### Ejecución del Sistema
1. Inicia el programa principal:
   ```bash
   python main.py
   ```

2. Usa la interfaz HMI para:
   - Configurar clases y coordenadas de depósito.
   - Ajustar área de trabajo.
   - Configurar velocidades del sistema de transporte.

### Flujo de Trabajo
1. Captura una imagen desde la cámara utilizando el botón en la interfaz.
2. El sistema procesa la imagen y clasifica los objetos dentro del área de trabajo.
3. Los resultados se envían al ESP32 para accionar el transporte hacia las coordenadas configuradas.

### Configuración HMI
- **Clases**: Define las clases y sus coordenadas.
- **Velocidades**: Ajusta la velocidad de la cinta transportadora.
- **Área de Trabajo**: Configura los límites del área de trabajo.

## Arquitectura del Proyecto

### Módulos Principales
1. **Servicios de Procesamiento de Imágenes**
   - Captura, corrección de distorsión y detección de objetos.

2. **Gestor de Modelo YOLO**
   - Manejo del modelo YOLO para detección y clasificación de objetos.

3. **HMI**
   - Interfaz gráfica para configuración y visualización.

4. **Controlador de Transporte**
   - Comunicación con el ESP32 para mover los objetos a las posiciones deseadas.

### Diagrama de Flujo
1. Captura de imagen desde la cámara.
2. Procesamiento de la imagen y detección de objetos con YOLO.
3. Filtro de objetos según área de trabajo y confianza.
4. Envio de instrucciones al ESP32 para mover los objetos.


