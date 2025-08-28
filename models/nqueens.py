import unconstrained.minizinc as mz

async def solve(n:int, options: mz.SolveOptions, **kwargs):
    """
    Solve the model with the given options
    """

    mzn = f"""
    % N-Queens satisfaction model
    include "alldifferent.mzn";
        
    int: n = {n};

    set of int: N = 1 .. n;

    % The Queen in column i is in row q[i]
    array [N] of var N: q; 
            
    % Each queen is in a different row
    constraint 
        alldifferent(q); 

    % Upwards diagonal
    constraint 
        alldifferent([ q[i] + i | i in N]); 

    % Downwards diagonal
    constraint 
        alldifferent([ q[i] - i | i in N]); 
    
    solve ::
        int_search(q, first_fail, indomain_min)
        satisfy;
    """

    async for result in mz.solve(mzn, options, **kwargs):
        if not result.has_solution:
            yield result
            continue

        array = result["q"]
        for i, row in enumerate(array):
            break
            # queen = model.queens.get(i)

        yield result


# def create_chart_data(model: Model):
#     records = []
#     for queen in model.queens:
#         records.append(
#             dict(
#                 n=model.n,
#                 queen=queen.number,
#                 y=queen.row,
#                 y2=queen.row + 1,
#                 x=queen.col,
#                 x2=queen.col + 1,
#             )
#         )
#     return records


# def plot(model: Model):
#     data = create_chart_data(model)
#     base = (
#         alt.Chart(data)
#         .encode(x=alt.X("x:O", axis=alt.Axis(grid=True, labels=False)))
#         .encode(y=alt.Y("y:O", axis=alt.Axis(grid=True, labels=False)))
#         .encode(x2=alt.X2("x2:O"))
#         .encode(y2=alt.Y2("y2:O"))
#     )

#     rects = base.mark_rect(color="black")
#     texts = base.mark_text(color="white", size=14).encode(text="queen:N")
#     chart = rects + texts
#     return chart
