function edges = compute_edges(face)

if isempty(face)
    edges=[];
    return;
end

[tmp,face] = check_face_vertex([],face);

if size(face,1)~=3
    error('Problem');
end
d = size(face,1);

edges = [];
for i=1:d
    sel = [i, mod(i,d)+1];
    edges = [edges, face(sel,:)];
end

I = find(edges(1,:)>edges(2,:));
J = find(edges(1,:)<=edges(2,:));
edges = [edges(end:-1:1,I), edges(:,J)];

m = max(edges(:))+100;
id = edges(1,:) + m*edges(2,:);

[tmp,I] = unique(id);
edges = edges(:,I);
