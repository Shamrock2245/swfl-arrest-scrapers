#!/bin/bash
# Extract all PDF form fields from all templates

OUTPUT_FILE="/home/ubuntu/shamrock-bail-bonds/pdf_field_mapping.md"
PDF_DIR="/home/ubuntu/shamrock-bail-bonds/pdf_analysis"

echo "# PDF Form Field Mapping - Shamrock Bail Bonds" > $OUTPUT_FILE
echo "" >> $OUTPUT_FILE
echo "Generated: $(date)" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

for pdf in "$PDF_DIR"/*.pdf; do
    filename=$(basename "$pdf")
    echo "## $filename" >> $OUTPUT_FILE
    echo "" >> $OUTPUT_FILE
    echo "| Field Name | Field Type |" >> $OUTPUT_FILE
    echo "|------------|------------|" >> $OUTPUT_FILE
    
    pdftk "$pdf" dump_data_fields 2>/dev/null | awk '
        /^FieldType:/ { type = $2 }
        /^FieldName:/ { 
            name = $2
            for(i=3; i<=NF; i++) name = name " " $i
            print "| " name " | " type " |"
        }
    ' >> $OUTPUT_FILE
    
    echo "" >> $OUTPUT_FILE
done

echo "Field mapping saved to $OUTPUT_FILE"
