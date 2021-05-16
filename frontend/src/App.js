import Typography from "@material-ui/core/Typography";
import Paper from "@material-ui/core/Paper";
import Search from "./Search";

function App() {
    return (
        <div className="App" style={{}}>
            <Paper
                elevation={10}
                variant="outlined"
                style={{
                    backgroundColor: "darkgray",
                    margin: "10px",
                }}
            >
                <Typography variant="h6" component="h2" style={{ margin: "5px" }}>
                    ETF Optimizer
                </Typography>
                <Typography variant="subtitle1" component="h2" style={{ marginLeft: "5px" }}>
                    Optimize an ETF portfolio by defining your own filters. Using ETF data from justETF and historical data from Refinitiv
                    Eikon.
                </Typography>
            </Paper>
            <Search />
        </div>
    );
}

export default App;
