import argparse
from rdflib import Graph, RDFS, RDF, OWL, Namespace

def get_prefix(uri,no_prefix=False):
    # Special handling for geo: vs geo1: rdflib mapping
    if 'www.w3.org/2003/01/' in str(uri):
        # Map both geo and geo1 to 'geo' for cleaner output
        if no_prefix:
            return str(uri).split('#')[-1]
        else:
            return f"geo_{uri.split('#')[-1]}"
    
    for prefix, ns in PREFIXES.items():
        if uri.startswith(ns):
            if no_prefix:
                return f"{uri[len(str(ns)):]}"
            else:
                return f"{prefix}_{uri[len(str(ns)):]}"
    return uri

def generate_class_diagram(graph, include_datatype_properties=True, no_prefix=False, incl_comments=False):
    mermaid = ['classDiagram']

    # Collect classes
    classes = set()
    for s, p, o in graph.triples((None, RDF.type, OWL.Class)):
        class_name = get_prefix(s,no_prefix)
        classes.add(class_name)

    # # Collect subclasses
    subclass_relationships = []
    for s, p, o in graph.triples((None, RDFS.subClassOf, None)):
        super_class = get_prefix(o,no_prefix)
        sub_class = get_prefix(s,no_prefix)
        if sub_class != super_class and super_class in classes:
            subclass_relationships.append((sub_class, super_class))


    # Collect object properties
    object_properties = {}
    for s, p, o in graph.triples((None, RDF.type, OWL.ObjectProperty)):
        property_name = get_prefix(s,no_prefix)
        if property_name not in object_properties:
            object_properties[property_name] = {'domains': [], 'ranges': [], 'label': property_name, 'comment': ''}


    
    # Collect datatype properties
    datatype_properties = {}
    for s, p, o in graph.triples((None, RDF.type, OWL.DatatypeProperty)):
        property_name = get_prefix(s,no_prefix)
        if property_name not in datatype_properties:
            datatype_properties[property_name] = {'domains': [], 'ranges': [], 'label': property_name, 'comment': ''}


    # Collect domains and ranges of properties
    for s, p, o in graph.triples((None, None, None)):
        if p == RDFS.domain:
            property_name = get_prefix(s,no_prefix)
            class_name = get_prefix(o,no_prefix)
            if property_name in object_properties:
                object_properties[property_name]['domains'].append(class_name)
            elif property_name in datatype_properties:
                datatype_properties[property_name]['domains'].append(class_name)
        elif p == RDFS.range:
            property_name = get_prefix(s,no_prefix)
            class_name = get_prefix(o,no_prefix)
            if property_name in object_properties:
                object_properties[property_name]['ranges'].append(class_name)
            elif property_name in datatype_properties:
                datatype_properties[property_name]['ranges'].append(class_name)

    # Collect labels and comments for properties
    for s, p, o in graph.triples((None, RDFS.label, None)):
        property_name = get_prefix(s,no_prefix)
        label = o.toPython()
        if property_name in object_properties:
            object_properties[property_name]['label'] = label
        elif property_name in datatype_properties:
            datatype_properties[property_name]['label'] = label

    if incl_comments:
        for s, p, o in graph.triples((None, RDFS.comment, None)):
            property_name = get_prefix(s,no_prefix)
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
            mermaid.append(f"{sub_class} --|> {super_class} : subClassOf")

    # Add object properties to Mermaid
    for prop_name, prop_info in object_properties.items():
        domains = prop_info['domains']
        ranges = prop_info['ranges']
        if not domains or not ranges:
            continue  # Skip properties without domain/range defined
        label = prop_info.get('label', prop_name)
        comment = prop_info.get('comment', '')
        # Handle multiple domains/ranges by creating separate edges
        for domain in domains:
            for range_val in ranges:
                line = f"{domain} --> {range_val} : {label}"
                if comment:
                    line += f'  // {comment}'
                mermaid.append(line)

    return "\n".join(mermaid)



def generate_graph_diagram(graph, include_datatype_properties=True, no_prefix=False, incl_comments=False):
    """Generates a Mermaid graph diagram."""
    mermaid = ["graph TD"]

    # Collect class nodes (only OWL.Class instances)
    classes = set()
    for s, p, o in graph.triples((None, RDF.type, OWL.Class)):
        class_name = get_prefix(s, no_prefix)
        classes.add(class_name)

    # Collect object property edges
    edges = []
    for s, p, o in graph.triples((None, RDF.type, OWL.ObjectProperty)):
        prop_name = get_prefix(s, no_prefix)
        # Get domain
        for s2, p2, o2 in graph.triples((s, RDFS.domain, None)):
            domain = get_prefix(o2, no_prefix)
            # Get range
            for s3, p3, o3 in graph.triples((s, RDFS.range, None)):
                # Only include if range is a class (not a datatype)
                range_uri = o3
                if str(range_uri).startswith('http://www.w3.org/2001/XMLSchema#') or str(range_uri).startswith('http://www.w3.org/2003/01/geo#'):
                    continue  # Skip datatype ranges
                range_name = get_prefix(range_uri, no_prefix)
                edges.append((domain, range_name, prop_name))

    # Add class nodes
    for cls in classes:
        mermaid.append(f"    {cls}")

    # Add edges with labels - use proper Mermaid syntax with label on arrow
    for from_node, to_node, label in edges:
        mermaid.append(f'    {from_node} -->|"{label}"| {to_node}')
    
    # Add subclass relationships
    for s, p, o in graph.triples((None, RDFS.subClassOf, None)):
        sub_class = get_prefix(s, no_prefix)
        super_class = get_prefix(o, no_prefix)
        if sub_class != super_class and super_class in classes:
            mermaid.append(f'    {sub_class} -->|"subClassOf"| {super_class}')
    
    if incl_comments:
        for s, p, o in graph.triples((None, RDFS.comment, None)):
            if p == RDFS.comment:
                property_name = get_prefix(s, no_prefix)
                comment = o.toPython()
                mermaid.append(f'    note over {property_name} : {comment}')

    return "\n".join(mermaid)


def generate_er_diagram(graph, include_datatype_properties=True, no_prefix=False, incl_comments=False):
    """Generates a Mermaid ER diagram."""
    mermaid = ['erDiagram']

    # Collect classes (entities)
    classes = set()
    for s, p, o in graph.triples((None, RDF.type, OWL.Class)):
        class_name = get_prefix(s,no_prefix)
        classes.add(class_name)

    # Collect object properties (relationships)
    object_properties = {}
    for s, p, o in graph.triples((None, RDF.type, OWL.ObjectProperty)):
        property_name = get_prefix(s,no_prefix)
        if property_name not in object_properties:
            object_properties[property_name] = {'domains': [], 'ranges': [], 'label': property_name, 'comment': ''}

    # Collect domains and ranges of properties
    for s, p, o in graph.triples((None, None, None)):
        if p == RDFS.domain:
            property_name = get_prefix(s,no_prefix)
            class_name = get_prefix(o,no_prefix)
            if property_name in object_properties:
                object_properties[property_name]['domains'].append(class_name)
        elif p == RDFS.range:
            property_name = get_prefix(s,no_prefix)
            range_uri = get_prefix(o,no_prefix)
            if property_name in object_properties:
                object_properties[property_name]['ranges'].append(range_uri)

    # Collect labels and comments for properties
    for s, p, o in graph.triples((None, RDFS.label, None)):
        property_name = get_prefix(s,no_prefix)
        label = o.toPython()
        if property_name in object_properties:
            object_properties[property_name]['label'] = label

    if incl_comments:
        for s, p, o in graph.triples((None, RDFS.comment, None)):
            property_name = get_prefix(s,no_prefix)
            comment = o.toPython()
            if property_name in object_properties:
                object_properties[property_name]['comment'] = comment

    # Add entities (classes)
    for cls in classes:
        mermaid.append(f'    {cls} {{}}')

    # Add relationships
    for prop_name, prop_info in object_properties.items():
        domains = prop_info['domains']
        ranges = prop_info['ranges']
        if not domains or not ranges:
            continue
        label = prop_info.get('label', prop_name)
        comment = prop_info.get('comment', '')
        for domain in domains:
            for range_val in ranges:
                mermaid.append(f'    {domain} ||--o{{ {range_val} : "{label}"')

    # Add subclass relationships
    subclass_relationships = []
    for s, p, o in graph.triples((None, RDFS.subClassOf, None)):
        super_class = get_prefix(o,no_prefix)
        sub_class = get_prefix(s,no_prefix)
        if sub_class != super_class and super_class in classes:
            subclass_relationships.append((sub_class, super_class))

    for sub_class, super_class in subclass_relationships:
        if sub_class != super_class and super_class in classes:
            mermaid.append(f'    {sub_class} ||--o{{ {super_class} : "subClassOf"')

    return "\n".join(mermaid)

def generate_mermaid_diagram(graph, diagram_type='classDiagram', include_datatype_properties=True, no_prefix=False, incl_comments=False):
    if diagram_type == 'classDiagram':
        return generate_class_diagram(graph, include_datatype_properties, no_prefix, incl_comments)
    elif diagram_type == 'erDiagram':
        return generate_er_diagram(graph, include_datatype_properties, no_prefix, incl_comments)
    elif diagram_type == 'graph TD':
        return generate_graph_diagram(graph, include_datatype_properties, no_prefix, incl_comments)
    else:
        raise ValueError(f"Unsupported diagram type: {diagram_type}")



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
    parser.add_argument("--diagram_type", choices=['classDiagram', 'erDiagram', 'graph TD'], default='classDiagram', help="Type of Mermaid diagram")
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