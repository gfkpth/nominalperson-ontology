import argparse
from rdflib import Graph, RDFS, RDF, OWL, Namespace

def get_prefix(uri):
    for prefix, ns in PREFIXES.items():
        if uri.startswith(ns):
            # if no_prefix:
            #     return f"{uri[len(str(ns)):]}"
            # else:
            return f"{prefix}:{uri[len(str(ns)):]}"
    return uri

def generate_mermaid_diagram(graph, diagram_type='classDiagram', include_datatype_properties=True, no_prefix=False):
    mermaid = [diagram_type]

    # Collect classes
    classes = set()
    for s, p, o in graph.triples((None, RDF.type, OWL.Class)):
        class_name = get_prefix(s)
        classes.add(class_name)

    # # Collect subclasses
    subclass_relationships = []
    for s, p, o in graph.triples((None, RDFS.subClassOf, None)):
        super_class = get_prefix(o)
        sub_class = get_prefix(s)
        if sub_class != super_class and super_class in classes:
            subclass_relationships.append((sub_class, super_class))


    # Collect object properties
    object_properties = {}
    for s, p, o in graph.triples((None, RDF.type, OWL.ObjectProperty)):
        property_name = get_prefix(s)
        if property_name not in object_properties:
            object_properties[property_name] = {'domains': [], 'ranges': []}


    
    # Collect datatype properties
    datatype_properties = {}
    for s, p, o in graph.triples((None, RDF.type, OWL.DatatypeProperty)):
        property_name = get_prefix(s)
        if property_name not in datatype_properties:
            datatype_properties[property_name] = {'domains': [], 'ranges': []}


    # Collect domains and ranges of properties
    for s, p, o in graph.triples((None, None, None)):
        if p == RDFS.domain:
            print(s + p + o)
            property_name = get_prefix(s)
            class_name = get_prefix(o)
            if property_name in object_properties:
                object_properties[property_name]['domains'].append(class_name)
            elif property_name in datatype_properties:
                datatype_properties[property_name]['domains'].append(class_name)
        elif p == RDFS.range:
            property_name = get_prefix(s)
            class_name = get_prefix(o)
            if property_name in object_properties:
                object_properties[property_name]['ranges'].append(class_name)
            elif property_name in datatype_properties:
                datatype_properties[property_name]['ranges'].append(class_name)

    print("Object properties")
    print(object_properties)
    print("Datatype props")
    print(datatype_properties)
    # Collect labels and comments for properties
    for s, p, o in graph.triples((None, RDFS.label, None)):
        if p == RDFS.label:
            property_name = get_prefix(s)
            label = o.toPython()
            if property_name in object_properties:
                object_properties[property_name]['label'] = label
            elif property_name in datatype_properties:
                datatype_properties[property_name]['label'] = label

    for s, p, o in graph.triples((None, RDFS.comment, None)):
        if p == RDFS.comment:
            property_name = get_prefix(s)
            comment = o.toPython()
            if property_name in object_properties:
                object_properties[property_name]['comment'] = comment
            elif property_name in datatype_properties:
                datatype_properties[property_name]['comment'] = comment

    # Add classes and datatype properties to Mermaid
    for cls in classes:
        mermaid.append(f"class {cls} {{")
        if include_datatype_properties:
            for prop_name, prop_info in datatype_properties.items():
                if cls in prop_info['domains']:
                    label = prop_info.get('label', prop_name)
                    comment = prop_info.get('comment', '')
                    line = f"{label} : {prop_info['ranges'][0]}"
                    if comment:
                        line += f'  // {comment}'
                    mermaid.append(line)
        mermaid.append("}")

    # Add subclass relationships to Mermaid
    for sub_class, super_class in subclass_relationships:
        if sub_class != super_class and super_class in classes:
            mermaid.append(f"{sub_class} --|> {super_class}")

    # Add object properties to Mermaid
    for prop_name, prop_info in object_properties.items():
        domains = ', '.join(prop_info['domains'])
        ranges = ', '.join(prop_info['ranges'])
        label = prop_info.get('label', prop_name)
        comment = prop_info.get('comment', '')
        mermaid.append(f"{domains} --> {ranges} : {label}")
        if comment:
            mermaid[-1] += f'  // {comment}'

    return "\n".join(mermaid)

def extract_namespaces(graph):
    namespaces = {}
    for prefix, uri in graph.namespace_manager.namespaces():
        namespaces[prefix] = uri
    return namespaces

def save_to_file(content, filename):
    with open(filename, 'w') as file:
        file.write(content)

def main():
    parser = argparse.ArgumentParser(description="Generate a Mermaid diagram from an RDF ontology.")
    parser.add_argument("input", help="Input Turtle file")
    parser.add_argument("output", help="Output Mermaid file")
    parser.add_argument("--diagram_type", choices=['classDiagram', 'graph TD'], default='classDiagram', help="Type of Mermaid diagram")
    parser.add_argument("--include_datatype_properties", action='store_true', help="Include datatype properties in the diagram")
    parser.add_argument("--no_prefix", action='store_true', help="Do not include prefixes for simpler presentation")

    args = parser.parse_args()

    g = Graph()
    g.parse(args.input)
    
#     for triple in sorted(g):
#         for expr in triple:
#             if 'RegionGlottolog' in expr:
#                 print(triple)
# #        print(triple)

    global PREFIXES
    PREFIXES = extract_namespaces(g)

    # if args.suppress_prefixes:
    #     # Replace prefix: with an empty string to suppress prefixes
    #     for k in PREFIXES.keys():
    #         PREFIXES[k] = ''


    mermaid_diagram = generate_mermaid_diagram(
        g, 
        diagram_type=args.diagram_type, 
        include_datatype_properties=args.include_datatype_properties,
        no_prefix=args.no_prefix
    )
    
    # Save to file
    save_to_file(mermaid_diagram, args.output)

if __name__ == "__main__":
    main()