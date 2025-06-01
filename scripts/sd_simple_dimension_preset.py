from modules import shared, scripts
from pathlib import Path
import gradio as gr
import logging
import re

# Get logger for this extension
logger = logging.getLogger(__name__)

class OptionMarkdown(shared.OptionInfo):
    def __init__(self, text):
        super().__init__(str(text).strip(), label='', component=lambda **kwargs: gr.Markdown(**kwargs))
        self.do_not_save = True

class Script(scripts.Script):
    def __init__(self):
        super().__init__()
        self.sdp_root = Path(scripts.basedir())
        self.default_path = self.sdp_root / 'simple-preset.txt'
        self._default_presets = None
        self._example_md = None
        
        # Initialize options
        self._init_options()

    def _init_options(self):
        """Initialize options templates lazily"""
        shared.options_templates.update(shared.options_section(('simple-dimension-preset', 'Simple Dimension Preset'), {
            "simple_dimension_preset_doc": OptionMarkdown(self.get_example_md()),
            "simple_dimension_preset_config": shared.OptionInfo(self.get_default_presets(), 'simple dimension preset', gr.Code),
        }))

    def get_default_presets(self):
        """Lazy load default presets"""
        if self._default_presets is None:
            try:
                if self.default_path.exists():
                    self._default_presets = self.default_path.read_text(encoding='utf-8')
                else:
                    self._default_presets = ""
                    logger.warning(f"Default preset file not found: {self.default_path}")
            except Exception as e:
                logger.error(f"Error reading default presets: {e}")
                self._default_presets = ""
        return self._default_presets

    def get_example_md(self):
        """Lazy load example markdown"""
        if self._example_md is None:
            try:
                example_path = self.sdp_root / 'examples.md'
                if example_path.exists():
                    self._example_md = example_path.read_text(encoding='utf-8')
                else:
                    self._example_md = "No examples available."
                    logger.warning(f"Examples file not found: {example_path}")
            except Exception as e:
                logger.error(f"Error reading examples: {e}")
                self._example_md = "Error loading examples."
        return self._example_md

    def title(self):
        return "Simple Dimension Preset"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        with gr.Group():
            preset_textbox = gr.Textbox(
                visible=False,
                lines=10,
                show_label=False,
                elem_id="simple_dimension_preset_holder",
                max_lines=50,  # Prevent excessive content
                placeholder="Enter preset configuration..."
            )

            preset_textbox.change(
                fn=self._save_preset_safe,
                inputs=[preset_textbox],
                outputs=[]
            )
        
        return [preset_textbox]

    def _validate_preset_content(self, content):
        """Validate preset content before saving"""
        if not isinstance(content, str):
            return False, "Content must be a string"
        
        # Check length (prevent extremely large files)
        if len(content) > 100000:  # 100KB limit
            return False, "Content too large (max 100KB)"
        
        # Basic validation - ensure it looks like valid preset format
        # You might want to add more specific validation based on your preset format
        if content.strip() and not re.match(r'^[\w\s\-_:.,\n\r\[\]{}()\'"=<>]+$', content):
            return False, "Content contains invalid characters"
        
        return True, "Valid"

    def _save_preset_safe(self, inputs):
        """Safely save preset with validation and error handling"""
        try:
            # Validate input
            is_valid, message = self._validate_preset_content(inputs)
            if not is_valid:
                logger.warning(f"Invalid preset content: {message}")
                return
            
            # Ensure directory exists
            self.default_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup if file exists
            if self.default_path.exists():
                backup_path = self.default_path.with_suffix('.txt.backup')
                try:
                    backup_path.write_text(self.default_path.read_text(encoding='utf-8'), encoding='utf-8')
                except Exception as e:
                    logger.warning(f"Could not create backup: {e}")
            
            # Write new content
            with self.default_path.open("w", encoding="utf-8") as file:
                file.write(inputs)
            
            # Update cached value
            self._default_presets = inputs
            
            # Update options template
            if 'simple_dimension_preset_config' in shared.options_templates:
                shared.options_templates['simple_dimension_preset_config'].value = inputs
            
            logger.info("Preset saved successfully")
            
        except PermissionError:
            logger.error(f"Permission denied writing to {self.default_path}")
        except OSError as e:
            logger.error(f"OS error saving preset: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving preset: {e}")

    def _saving_preset(self, inputs):
        """Legacy method name for backwards compatibility"""
        return self._save_preset_safe(inputs)
