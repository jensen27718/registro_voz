import os
import json
import traceback
from PIL import Image

try:
    import google.generativeai as genai
    GEMINI_OCR_AVAILABLE = True
except ImportError:
    GEMINI_OCR_AVAILABLE = False

GEMINI_PROMPT = """
Eres un asistente de IA experto en la extracción de datos de pedidos a partir de imágenes. Tu objetivo es analizar la imagen de un pedido, que puede estar escrita a mano o impresa, y convertirla en un array JSON estructurado. Tu precisión es fundamental.

Tu única salida debe ser un array JSON válido, sin texto adicional, explicaciones ni formato ```json```.

### ESTRUCTURA DE SALIDA REQUERIDA ###
Cada objeto en el array JSON debe representar un único tipo de producto (una combinación de referencia, tamaño y color) y debe contener las siguientes claves:
- "ref": (string) La referencia o código del producto.
- "qty": (integer) La cantidad de unidades para ese producto.
- "tamaño": (string) El nombre del tamaño. **Este campo es crítico y DEBE ser uno de los tres valores exactos listados a continuación.**
- "color": (string) El nombre del color.

### REGLAS DE NEGOCIO Y LÓGICA DE EXTRACCIÓN ###

1.  **ORDEN DE LOS ITEMS:** Procesa la imagen y genera los objetos JSON en el mismo orden en que los items aparecen visualmente en el documento, de arriba hacia abajo y de izquierda a derecha.

2.  **MAPEADO DE TAMAÑO (REGLA ESTRICTA):** Tu tarea más importante es asignar el `tamaño` correcto. Utiliza las siguientes pistas visuales para determinar cuál de los tres nombres de tamaño oficiales usar:
    *   Si el contexto indica "Grande", "grandes", "25cm", o "19cm", el valor de `tamaño` DEBE SER **"Grande (19x25cm)"**.
    *   Si el contexto indica "Mediano", "medianos", o "15cm", el valor de `tamaño` DEBE SER **"Mediano (19x15cm)"**.
    *   Si el contexto indica "Pequeño", "pequeños", o "14,5cm", el valor de `tamaño` DEBE SER **"Pequeño (14,5x14,3cm)"**.
    
2.1  **MAPEADO DE Colores (REGLA ESTRICTA):** Tu tarea más importante es asignar el `color` correcto. Utiliza las siguientes pistas visuales para determinar cuál de los colores usar:
    *   Si el contexto indica " Dorado Metalizado", " Dorado Metalizados", " Dorado Metal", el valor de `color` DEBE SER **"Dorado Mailan"**.
    *   Si el contexto indica " Oro rosa Metalizado", " Oro rosa Metalizados", " Oro rosa Metal", el valor de `color` DEBE SER **"Oro rosa Mailan"**.
    *   Si el contexto indica " Plateado Metalizado", " Plateado Metalizados", " Plateado Metal", el valor de `color` DEBE SER **"Plateado Mailan"**.
    *   Si el contexto indica " Dorado Vinilo", " Dorados Vinilo", el valor de `color` DEBE SER **"Dorado"**.
     
3.  **ITEMS IMPLÍCITOS Y AGRUPACIONES (MUY IMPORTANTE):**
    *   Presta mucha atención a listas de referencias que no tienen atributos individuales.
    *   Si ves una lista de referencias y, al lado, texto descriptivo (ej: "Negro de 25cm") conectado por una **llave, línea o flecha**, DEBES aplicar esos atributos a **CADA UNA de las referencias** en esa lista.
    *   En estos grupos, si las referencias individuales no tienen una cantidad explícita (como `x3`), asume que la cantidad (`qty`) es 1 para cada una. Ignora números grandes en círculos a menos que esté claramente indicado como un multiplicador para el grupo.

4.  **DESGLOSE DE ITEMS:** Si una sola línea de pedido contiene múltiples productos (ej. "Ref 947: 6 negros y 6 dorados"), debes crear un objeto JSON separado para cada producto.

5.  **ATRIBUTOS GLOBALES Y DE GRUPO:** Analiza el contexto de la imagen. Si un atributo (como un tamaño o un color) se aplica a un grupo de referencias, asigna ese atributo a todos los items de dicho grupo, a menos que un item tenga su propio atributo específico que lo anule.

6.  **CANTIDAD POR DEFECTO:** Si a una referencia no se le asocia explícitamente una cantidad, asume que la cantidad (`qty`) es 1.

7.  **FILTRADO DE RUIDO:** Ignora cualquier texto o número que no sea parte de la descripción de un producto, como precios, totales, fechas, nombres de clientes o notas de pago.

### EJEMPLO DE PROCESAMIENTO DE GRUPO ###
Si la imagen muestra una lista de referencias:
1127
1144
1145
Y al lado, conectado por una llave, dice: "Negro de 25cm"

Tu salida JSON DEBE incluir:
[
  {"ref": "1127", "qty": 1, "tamaño": "Grande (19x25cm)", "color": "Negro"},
  {"ref": "1144", "qty": 1, "tamaño": "Grande (19x25cm)", "color": "Negro"},
  {"ref": "1145", "qty": 1, "tamaño": "Grande (19x25cm)", "color": "Negro"},
  ... (y así sucesivamente para todos los items del grupo)
]
"""


class GeminiOCRProcessor:
    """Procesa imágenes de pedidos para extraer referencias usando Gemini."""

    def __init__(self, api_key, available_colors=None):
        self.is_available = False
        self.available_colors = available_colors or []
        self.prompt = GEMINI_PROMPT
        self.model = None

        if not GEMINI_OCR_AVAILABLE:
            print("ADVERTENCIA: Librería 'google-generativeai' no encontrada. OCR con Gemini no disponible.")
            return

        if not api_key:
            print("ADVERTENCIA: No se proporcionó una clave API de Gemini. OCR con Gemini no disponible.")
            return

        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.is_available = True
            print("Cliente de Gemini AI para OCR inicializado correctamente.")
        except Exception as e:
            print(f"Error inicializando el cliente de Gemini AI: {e}")

    def _find_best_color_match(self, color_text_from_ia):
        if not color_text_from_ia or not isinstance(color_text_from_ia, str):
            return None

        normalized_ia_color = color_text_from_ia.lower().strip()
        if not normalized_ia_color:
            return None

        for config_color in self.available_colors:
            if normalized_ia_color == config_color.lower():
                return config_color

        potential_matches = []
        for config_color in self.available_colors:
            if config_color.lower() in normalized_ia_color:
                potential_matches.append(config_color)

        if potential_matches:
            return max(potential_matches, key=len)

        return None

    def process_image_to_extract_data(self, image_file_path):
        if not self.is_available or not self.model:
            return [], "El cliente de OCR con Gemini no está disponible o no se inicializó correctamente."

        try:
            image = Image.open(image_file_path)
            response = self.model.generate_content([self.prompt, image])
            cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "").strip()
            parsed_data = json.loads(cleaned_response_text)

            if not isinstance(parsed_data, list):
                return [], "La IA no devolvió una lista de items en formato JSON."

            colores_config = self.available_colors
            default_color_name = colores_config[0] if colores_config else "Negro"
            default_tamano_name = "Grande (19x25cm)"

            registros_finales = []
            for item in parsed_data:
                if not isinstance(item, dict) or 'ref' not in item or 'qty' not in item:
                    continue

                color_ia = item.get('color')
                matched_color = self._find_best_color_match(color_ia)
                final_color = matched_color if matched_color else default_color_name

                registros_finales.append({
                    'ref': str(item.get('ref', '')).strip().upper(),
                    'qty': int(item.get('qty', 1)),
                    'tamaño': item.get('tamaño', default_tamano_name),
                    'color': final_color,
                })

            if not registros_finales:
                return [], "No se encontraron items válidos en la imagen usando la IA."

            return registros_finales, None

        except json.JSONDecodeError:
            error_msg = f"Error de Gemini OCR: La respuesta no era un JSON válido."
            return [], error_msg
        except Exception as e:
            error_msg = f"Error durante el procesamiento con Gemini OCR: {e}"
            traceback.print_exc()
            return [], error_msg

