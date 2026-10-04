function genus=calc_genus(vert,face)

edges = compute_edges(face);
genus=(2-(length(vert)-length(edges)+length(face)))/2;

end
