import argparse
from rdflib import Graph, RDFS, RDF, OWL, Namespace

def get_prefix(uri,no_prefix=False):
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
            object_properties[property_name] = {'domains': [], 'ranges': []}


    
    # Collect datatype properties
    datatype_properties = {}
    for s, p, o in graph.triples((None, RDF.type, OWL.DatatypeProperty)):
        property_name = get_prefix(s,no_prefix)
        if property_name not in datatype_properties:
            datatype_properties[property_name] = {'domains': [], 'ranges': []}


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
        if p == RDFS.label:
            property_name = get_prefix(s,no_prefix)
            label = o.toPython()
            if property_name in object_properties:
                object_properties[property_name]['label'] = label
            elif property_name in datatype_properties:
                datatype_properties[property_name]['label'] = label

    if incl_comments:
        for s, p, o in graph.triples((None, RDFS.comment, None)):
            if p == RDFS.comment:
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
        domains = ', '.join(prop_info['domains'])
        ranges = ', '.join(prop_info['ranges'])
        label = prop_info.get('label', prop_name)
        comment = prop_info.get('comment', '')
        mermaid.append(f"{domains} --> {ranges} : {label}")
        if comment:
            mermaid[-1] += f'  // {comment}'

    return "\n".join(mermaid)



def generate_graph_diagram(graph, include_datatype_properties=True, no_prefix=False, incl_comments=False):
    """Generates a Mermaid graph diagram."""
    mermaid = ["graph TD"]

    # Collect nodes
    nodes = set()
    for s, p, o in graph.triples((None, RDF.type, None)):
        node_name = get_prefix(s, no_prefix)
        nodes.add(node_name)

    # Collect edges (relationships)
    edges = []
    for s, p, o in graph.triples((None, None, None)):
        if p == RDFS.subClassOf:  # treat subclassof as edges
            from_node = get_prefix(s, no_prefix)
            to_node = get_prefix(o, no_prefix)
            edges.append((from_node, to_node, "subClassOf"))
        elif p == RDFS.domain:
            from_node = get_prefix(s, no_prefix)
            to_node = get_prefix(o, no_prefix)
            edges.append((from_node, to_node, "domain"))
        elif p == RDFS.range:
            from_node = get_prefix(s, no_prefix)
            to_node = get_prefix(o, no_prefix)
            edges.append((from_node, to_node, "range"))
        else:  # treat all other properties as edges
            from_node = get_prefix(s, no_prefix)
            to_node = get_prefix(o, no_prefix)
            edges.append((from_node, to_node, "related"))  # generic relation


    # Add node definitions
    for node in nodes:
        label = get_prefix(node, no_prefix)  # use prefixed or local name
        mermaid.append(f"{node} [{label}];")

    # Add edge definitions
    for from_node, to_node, relation in edges:
        mermaid.append(f"{from_node} --> {to_node};")
    
    if incl_comments:
        for s, p, o in graph.triples((None, RDFS.comment, None)):
            if p == RDFS.comment:
                property_name = get_prefix(s, no_prefix)
                comment = o.toPython()
                # Find the corresponding node and add the comment as a tooltip.
                # This part is tricky because we need to find the node that the comment is associated with.
                # This implementation assumes the comment is directly associated with the node in the graph
                # and adds it as a tooltip.  You may need to adjust this based on your data model.
                node_to_add_comment = get_prefix(s, no_prefix) # the node itself

                mermaid.append(f"/* {node_to_add_comment} : {comment} */")


    return "\n".join(mermaid)


def generate_mermaid_diagram(graph, diagram_type='classDiagram', include_datatype_properties=True, no_prefix=False, incl_comments=False):
    if diagram_type == 'classDiagram':
        return generate_class_diagram(graph, include_datatype_properties, no_prefix, incl_comments)
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